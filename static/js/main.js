import { Recorder } from "./recorder.js";

(() => {
    document.addEventListener('DOMContentLoaded', async () => {
        let record_form                     = document.getElementById('record_form');
        let elderspeak_score                = document.getElementById('elderspeak_score');

        if(record_form) {
            let audio_elem;
            let audio_result;
            let has_recording               = false;
            let recorder                    = await Recorder();
            let record_black_div            = document.getElementById('record_black_div');
            let record_red_div              = document.getElementById('record_red_div');
            let record_audio_div            = document.getElementById('record_audio_div');

            record_black_div.addEventListener('click', async (e) => {
                e.preventDefault();
                await recorder.start();
                has_recording       = false;

                record_black_div.classList.add('hidden');
                record_red_div.classList.remove('hidden');
            });

            record_red_div.addEventListener('click', async (e) => {
                e.preventDefault();

                audio_result                = await recorder.stop();
                has_recording               = true;
                
                audio_elem                  = record_audio_div.querySelector('audio');
                audio_elem.setAttribute('src', audio_result.audio_url);
                audio_elem.play();

                record_red_div.classList.add('hidden');
                record_audio_div.classList.remove('hidden');
            });

            record_audio_div.querySelector('button').addEventListener('click', async (e) => {
                e.preventDefault();
                audio_elem.pause();
                has_recording               = false;
                recorder                    = await Recorder();

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

                const gebruiker             = await import('https://openfpcdn.io/fingerprintjs/v3.3.2/esm.min.js')
                                                .then(FingerprintJS => FingerprintJS.load())
                                                .then(fp => fp.get());
                const bowser                = window.bowser.getParser(window.navigator.userAgent);
                const fd                    = new FormData(record_form);

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
        } else if(elderspeak_score) { 
            let ok_sign                     = `<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>`;
            let ko_sign                     = `<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>`;

            let recieved_and_set;
            const viewables                 = {
                opnameduur:             document.getElementById('opnameduur'),
                geslacht:               document.getElementById('geslacht'),
                leeftijd:               document.getElementById('leeftijd'),
                langzaam_spreken:       document.getElementById('langzaam_spreken'),
                verhoogd_stemvolume:    document.getElementById('verhoogd_stemvolume'),
                verm_gram_complex:      document.getElementById('verm_gram_complex'),
                aantal_verkleinwoorden: document.getElementById('aantal_verkleinwoorden'),
                aantal_collectieve_voornaamwoorden: document.getElementById('aantal_collectieve_voornaamwoorden'),
                aantal_bevestig_tussenwerpsels: document.getElementById('aantal_bevestig_tussenwerpsels'),
                verhoogde_toonhoogte:   document.getElementById('verhoogde_toonhoogte'),
                herhaling:              document.getElementById('herhaling'),
            };
            //const viewables_length = Object.entries(viewables).length;
            const viewables_length = 4;
            
            const poll_server = () => {
                console.log('polling...');

                recieved_and_set = 0;

                fetch(window.location.pathname + '/json')
                .then(r => r.json())
                .then(r => {
                    if (r[0].geslacht != null) {
                        viewables.geslacht.innerText = r[0].geslacht;
                        recieved_and_set++;
                    }

                    if (r[0].leeftijd != null) {
                        viewables.leeftijd.innerText = r[0].leeftijd;
                        recieved_and_set++;
                    }

                    if (r[0].aantal_collectieve_voornaamwoorden  != null) {
                        viewables.aantal_collectieve_voornaamwoorden.innerText = r[0].aantal_collectieve_voornaamwoorden;
                        recieved_and_set++;
                    }

                    if (r[0].aantal_bevestigende_tussenwerpsels != null) {
                        viewables.aantal_bevestig_tussenwerpsels.innerText = r[0].aantal_bevestigende_tussenwerpsels;
                        recieved_and_set++;
                    }
                    
                    console.log('Recieved: ' + recieved_and_set);

                    if (recieved_and_set < viewables_length) {
                        setTimeout(poll_server, 2000);
                    }
                })
                .catch((reason) => {
                    alert('Er liep iets mis. Fout = ' + reason);
                    window.location.href = '';
                });
            };
            poll_server();
        }
    });
})();