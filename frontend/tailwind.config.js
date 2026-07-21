/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#B40A14',      // Secure-Eye red
        accent:  '#1E78DC',      // Secure-Eye blue
        surface: '#1a0508',      // dark red surface
      }
    }
  },
  plugins: [],
}
