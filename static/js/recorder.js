const Recorder = () =>
    new Promise(async resolve => {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const media_recorder = new MediaRecorder(stream);
        const audio_chunks = [];

        media_recorder.addEventListener("dataavailable", event => {
            audio_chunks.push(event.data);
        });

        const start = () => media_recorder.start();

        const stop = () =>
            new Promise(resolve => {
                media_recorder.addEventListener("stop", () => {
                    const audio_blob = new Blob(audio_chunks, { type: 'audio/wav' });
                    const audio_url = URL.createObjectURL(audio_blob);
                    resolve({ audio_blob, audio_url });
                });

                media_recorder.stop();
            });

        resolve({ start, stop });
    });

export { Recorder }