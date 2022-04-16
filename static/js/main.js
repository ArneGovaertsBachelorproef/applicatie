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

                fd.append('opname', audio_result.audio_blob, 'leeftijdsgenoot_opname_'
                            + new Date().toISOString().replaceAll(':','-').split('.')[0] + '_' + gebruiker.visitorId + '.wav');
                
                fetch('/app', {
                    method: 'POST',
                    body: fd,
                })
                .then(r => r.json())
                .then(r => {
                    if (r.success) {
                        // redirect naar resultaat
                    } else {
                        alert('Er liep iets mis. Fout = ' + r.error);
                    }
                })
                .catch((reason) => {
                    alert('Er liep iets mis. Fout = ' + reason);
                });                
            });
        }
    });


    /*
    const gotoResultAction = () => {
        document.getElementById('card').innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="animate-spin -ml-1 mr-3 h-16 text-black">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>`;

        import('https://openfpcdn.io/fingerprintjs/v3.3.2/esm.min.js')
        .then(FingerprintJS => FingerprintJS.load())
        .then(fp => fp.get())
        .then(gebruiker => {
            const bowser = window.bowser.getParser(window.navigator.userAgent);
            const fd = new FormData();
            fd.append('browser', bowser.getBrowserName() + ' ' + bowser.getBrowserVersion());
            fd.append('os', bowser.getOSName() + ' ' + bowser.getOSVersion());
            fd.append('platform', bowser.getPlatformType());
            fd.append('opname', audio_result.audio_blob, 'leeftijdsgenoot_opname_'
                            + new Date().toISOString().replaceAll(':','-').split('.')[0] + '_' + gebruiker.visitorId + '.wav');
            
            fetch('/app', {
                method: 'POST',
                body: fd,
            })
            .then(r => r.json())
            .then(r => {
                if (r.success) {
                    // redirect naar resultaat
                } else {
                    alert('Er liep iets mis. Fout = ' + r.error)
                }
            })
            .catch((reason) => {
                alert('Er liep iets mis. Fout = ' + reason)
            });
        })
        .catch((reason) => {
            alert('Er liep iets mis. Fout = ' + reason)
        });
    };

    const recordAction = async () => {
        switch (recording) {
            case 4:

            break;
            case 2:
                audio_result = await recorder.stop();
    
                recordBtn.innerText = 'opnieuw';
    
                let recordAudio = new Audio();
                recordAudio.src = audio_result.audio_url;
                recordAudio.controls = 'true';
                audio_resultDiv.innerText = '';
                audio_resultDiv.insertAdjacentElement('beforeend', recordAudio);
                recordAudio.play();
    
                let gotoResultBtn = document.createElement('button');
                gotoResultBtn.innerText = 'naar resultaat';
                gotoResultBtn.addEventListener('click', gotoResultAction);
                gotoResultDiv.innerText = '';
                gotoResultDiv.insertAdjacentElement('beforeend', gotoResultBtn);
    
                recording = 1;
                recorder = await Recorder();
            break;
            case 1:
                audio_resultDiv.innerText = '';
                recordBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>`;
                gotoResultDiv.innerText = '';
    
                recording = 0;
            break;
            default:
                audio_resultDiv.innerText = '';
                recordBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-red-700" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clip-rule="evenodd" />
                </svg>`;
                gotoResultDiv.innerText = '';
    
                await recorder.start();
                recording = 2;
                break;
        }
    };
    
    document.addEventListener('DOMContentLoaded', async () => {
        recordBtn      = document.getElementById('record');
        audio_resultDiv = document.getElementById('audio_result');
        gotoResultDiv  = document.getElementById('gotoResult');
    
        if (recordBtn) {
            recording = 0;
            recorder = await Recorder();
    
            recordBtn.addEventListener('click', recordAction);
        }
    });*/
})();