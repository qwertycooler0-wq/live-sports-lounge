/* ── Game Audio Engine (Web Audio API — no external files) ──────── */
class GameAudio {
    constructor() {
        this.ctx = null;
        this.enabled = false;
        this.volume = 0.5;
        this._loadPrefs();
    }

    _loadPrefs() {
        this.enabled = localStorage.getItem('sound_enabled') === '1';
        const v = parseFloat(localStorage.getItem('sound_volume'));
        if (!isNaN(v)) this.volume = v;
    }

    enable() {
        if (!this.ctx) this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        this.enabled = true;
        localStorage.setItem('sound_enabled', '1');
        this._updateIcon();
    }

    disable() {
        this.enabled = false;
        localStorage.setItem('sound_enabled', '0');
        this._updateIcon();
    }

    toggle() {
        if (this.enabled) this.disable(); else this.enable();
    }

    setVolume(v) {
        this.volume = v;
        localStorage.setItem('sound_volume', v.toString());
    }

    _updateIcon() {
        const btn = document.getElementById('sound-toggle');
        if (!btn) return;
        const on = btn.querySelector('.icon-sound-on');
        const off = btn.querySelector('.icon-sound-off');
        if (on && off) {
            on.classList.toggle('hidden', !this.enabled);
            off.classList.toggle('hidden', this.enabled);
        }
    }

    _ensureCtx() {
        if (!this.enabled) return false;
        if (!this.ctx) this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        if (this.ctx.state === 'suspended') this.ctx.resume();
        return true;
    }

    crowdRoar(intensity) {
        if (!this._ensureCtx()) return;
        const dur = 0.3 + intensity * 0.5;
        const bufSize = this.ctx.sampleRate * dur;
        const buf = this.ctx.createBuffer(1, bufSize, this.ctx.sampleRate);
        const data = buf.getChannelData(0);
        for (let i = 0; i < bufSize; i++) data[i] = (Math.random() * 2 - 1);

        const src = this.ctx.createBufferSource();
        src.buffer = buf;

        const bp = this.ctx.createBiquadFilter();
        bp.type = 'bandpass';
        bp.frequency.value = 1200;
        bp.Q.value = 0.5;

        const gain = this.ctx.createGain();
        const now = this.ctx.currentTime;
        const vol = this.volume * intensity * 0.4;
        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(vol, now + 0.05);
        gain.gain.setValueAtTime(vol, now + dur * 0.6);
        gain.gain.linearRampToValueAtTime(0, now + dur);

        src.connect(bp).connect(gain).connect(this.ctx.destination);
        src.start(now);
        src.stop(now + dur);
    }

    buzzer() {
        if (!this._ensureCtx()) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        osc.type = 'square';
        osc.frequency.setValueAtTime(220, now);
        osc.frequency.linearRampToValueAtTime(200, now + 1.5);

        const gain = this.ctx.createGain();
        const vol = this.volume * 0.25;
        gain.gain.setValueAtTime(vol, now);
        gain.gain.setValueAtTime(vol, now + 1.2);
        gain.gain.linearRampToValueAtTime(0, now + 1.5);

        osc.connect(gain).connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 1.5);
    }

    whistleBlast() {
        if (!this._ensureCtx()) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.value = 3000;

        const gain = this.ctx.createGain();
        const vol = this.volume * 0.15;
        gain.gain.setValueAtTime(vol, now);
        gain.gain.linearRampToValueAtTime(0, now + 0.2);

        osc.connect(gain).connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.2);
    }

    crowdGasp() {
        if (!this._ensureCtx()) return;
        const dur = 0.4;
        const bufSize = this.ctx.sampleRate * dur;
        const buf = this.ctx.createBuffer(1, bufSize, this.ctx.sampleRate);
        const data = buf.getChannelData(0);
        for (let i = 0; i < bufSize; i++) data[i] = (Math.random() * 2 - 1);

        const src = this.ctx.createBufferSource();
        src.buffer = buf;

        const bp = this.ctx.createBiquadFilter();
        bp.type = 'bandpass';
        bp.frequency.value = 1500;
        bp.Q.value = 1;

        const gain = this.ctx.createGain();
        const now = this.ctx.currentTime;
        const vol = this.volume * 0.2;
        gain.gain.setValueAtTime(0, now);
        gain.gain.linearRampToValueAtTime(vol, now + 0.05);
        gain.gain.linearRampToValueAtTime(0, now + dur);

        src.connect(bp).connect(gain).connect(this.ctx.destination);
        src.start(now);
        src.stop(now + dur);
    }
}

const gameAudio = new GameAudio();

// Wire up sound toggle button
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('sound-toggle');
    const slider = document.getElementById('volume-slider');
    if (btn) {
        btn.addEventListener('click', () => gameAudio.toggle());
        gameAudio._updateIcon();
    }
    if (slider) {
        slider.value = gameAudio.volume * 100;
        slider.addEventListener('input', (e) => {
            gameAudio.setVolume(parseInt(e.target.value) / 100);
        });
        if (btn) {
            btn.addEventListener('mouseenter', () => slider.classList.remove('hidden'));
            slider.addEventListener('mouseleave', () => slider.classList.add('hidden'));
        }
    }
});
