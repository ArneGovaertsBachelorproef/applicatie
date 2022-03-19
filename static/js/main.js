import { Recorder } from "./recorder.js";

document.addEventListener('DOMContentLoaded', async () => {
    let recordBtn = document.getElementById('record');
    let recording = false;
    let recorder = await Recorder();

    if(recordBtn) {
        recordBtn.addEventListener('click', async (e) => {
            e.preventDefault();
    
            if(!recording) {
                recordBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-red-700" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clip-rule="evenodd" />
                </svg>`;
    
                await recorder.start();
    
                recording = true;
            } else {
                recordBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>`;
    
                let result = await recorder.stop();
                let audio = new Audio();
                audio.src = result.audioUrl;
                audio.controls = "true";
                let holder = document.getElementById('audioResult');
                holder.innerText = '';
                holder.insertAdjacentElement('beforeend', audio);
                audio.play();
    
                recording = false;
                recorder = await Recorder();
            }
            
            return false;
        })
    }
});