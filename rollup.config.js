import nodent from 'rollup-plugin-nodent';
import { terser } from "rollup-plugin-terser";

export default {
    input: './static/js/main.js',
    output: {
      file: './dist/js/bundle.js',
      format: 'es',
      plugins: [nodent(), terser()],
    },
    external: ['https://openfpcdn.io/fingerprintjs/v3.3.2/esm.min.js']
};