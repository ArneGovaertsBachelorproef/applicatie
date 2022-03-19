import nodent from 'rollup-plugin-nodent';
import { terser } from "rollup-plugin-terser";

export default {
    input: './static/js/main.js',
    output: {
      file: './dist/js/bundle.js',
      format: 'es',
      plugins: [nodent()/*, terser()*/]
    }
};