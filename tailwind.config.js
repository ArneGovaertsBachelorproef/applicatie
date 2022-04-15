module.exports = {
  content: ["./templates/*.html", "./templates/app/*.html", "./templates/auth/*.html", "./static/js/*.js"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms')
  ],
}
