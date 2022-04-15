npx tailwindcss -i ./static/input.css -o ./dist/style.css;

Copy-Item "./static/brooke-cagle-NoRsyXmHGpI-unsplash.jpg" -Destination "./dist/brooke-cagle-NoRsyXmHGpI-unsplash.jpg";
Copy-Item "./static/HOGENT_Logo_Pos_rgb.png" -Destination "./dist/HOGENT_Logo_Pos_rgb.png";

rollup --config rollup.config.js;