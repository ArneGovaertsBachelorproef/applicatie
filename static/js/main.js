import { Recorder } from "./recorder.js";

(() => {
    let audio_elem;
    let audio_result;
    let recorder;
    let record_black_div;
    let record_red_div;
    let record_audio_div;
    let record_form;
    let has_recording = false;

    document.addEventListener('DOMContentLoaded', async () => {
        record_form = document.getElementById('record_form')

        if(record_form) {
            recorder         = await Recorder();
            record_black_div = document.getElementById('record_black_div');
            record_red_div   = document.getElementById('record_red_div');
            record_audio_div = document.getElementById('record_audio_div');

            record_black_div.addEventListener('click', async (e) => {
                e.preventDefault();
                await recorder.start();
                has_recording = false;

                record_black_div.classList.add('hidden');
                record_red_div.classList.remove('hidden');
            });

            record_red_div.addEventListener('click', async (e) => {
                e.preventDefault();

                audio_result = await recorder.stop();
                has_recording = true;
                
                audio_elem = record_audio_div.querySelector('audio');
                audio_elem.setAttribute('src', audio_result.audio_url);
                audio_elem.play();

                record_red_div.classList.add('hidden');
                record_audio_div.classList.remove('hidden');
            });

            record_audio_div.querySelector('button').addEventListener('click', async (e) => {
                e.preventDefault();
                audio_elem.pause();
                has_recording = false;
                
                recorder = await Recorder();

                record_audio_div.classList.add('hidden');
                record_black_div.classList.remove('hidden');
            });

            record_form.addEventListener('submit', async (e) => {
                e.preventDefault();

                if(!has_recording) {
                    alert('Er dient eerst een opname gemaakt te worden.');
                    return;
                }

                document.querySelectorAll('#record_form > div')[0].classList.add('hidden');
                document.querySelector('#record_form > button').classList.add('hidden');
                document.querySelectorAll('#record_form > div')[1].classList.remove('hidden');

                const gebruiker = await import('https://openfpcdn.io/fingerprintjs/v3.3.2/esm.min.js')
                                .then(FingerprintJS => FingerprintJS.load())
                                .then(fp => fp.get());
                const bowser = window.bowser.getParser(window.navigator.userAgent);
                const fd = new FormData(record_form);

                fd.append('browser', bowser.getBrowserName() + ' ' + bowser.getBrowserVersion());
                fd.append('os', bowser.getOSName() + ' ' + bowser.getOSVersion());
                fd.append('platform', bowser.getPlatformType());
                fd.append('bezoeker_id', gebruiker.visitorId);

                fd.append('opname', audio_result.audio_blob, 'opname_' + new Date().toISOString().replaceAll(':','-') + '_' + gebruiker.visitorId + '.flac');
                
                fetch('/app', {
                    method: 'POST',
                    body: fd,
                })
                .then(r => r.json())
                .then(r => {
                    if (r.success) {
                        window.location.href = r.redirect_url;
                    } else {
                        alert('Er liep iets mis. Fout = ' + r.error);
                        window.location.href = '';
                    }
                })
                .catch((reason) => {
                    alert('Er liep iets mis. Fout = ' + reason);
                    window.location.href = '';
                });                
            });
        }
    });
})();