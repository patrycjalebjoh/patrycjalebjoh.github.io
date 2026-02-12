# Patrycja Lebiecka-Johansen - Academic Website

This is the source code for my personal academic website, hosted on GitHub Pages.
The site is fully static and features automatic publication updates from Google Scholar and ORCID.

## Features
- **Automated Data Fetching**: A Python script fetches publications weekly.
- **Modern Design**: Responsive, glassmorphism-inspired UI with dark mode.
- **Maintenance Free**: GitHub Actions handle the data updates.

## Local Development

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/patrycjalebjoh/patrycjalebjoh.github.io.git
    cd patrycjalebjoh.github.io
    ```

2.  **Serve the site**:
    You can use any static file server. For example:
    ```bash
    npx serve
    # OR
    python3 -m http.server
    ```
    Open `http://localhost:3000` (or the port shown/8000).

## Configuration

### Manual Trigger for Updates
To update publications immediately without waiting for the weekly schedule:
1.  Go to the **Actions** tab on GitHub.
2.  Select **Update Publications**.
3.  Click **Run workflow**.

### Customizing Bio
Edit `index.html` to update the "About" section text.

### Styles
Edit `assets/css/style.css` to change the visual theme.

## License
MIT
