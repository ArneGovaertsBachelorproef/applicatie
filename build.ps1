npx tailwindcss -i ./static/input.css -o ./dist/style.css
& Copy-Item "./static/brooke-cagle-NoRsyXmHGpI-unsplash.jpg" -Destination "./dist/brooke-cagle-NoRsyXmHGpI-unsplash.jpg"
& rollup --config rollup.config.js