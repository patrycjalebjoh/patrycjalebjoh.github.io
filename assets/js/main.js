document.addEventListener('DOMContentLoaded', () => {
    const pubListContainer = document.getElementById('publication-list');
    const MY_NAME = "Patrycja Lebiecka-Johansen";

    async function loadPublications() {
        try {
            const response = await fetch('assets/data/publications.json');
            if (!response.ok) throw new Error('Failed to load publications');
            const publications = await response.json();
            renderPublications(publications);
        } catch (error) {
            console.error('Error:', error);
            pubListContainer.innerHTML = '<p>Unable to load publications at this time.</p>';
        }
    }

    function renderPublications(pubs) {
        pubListContainer.innerHTML = '';

        // Sort by year desc ensuring logic consistency if not already sorted
        pubs.sort((a, b) => b.year - a.year);

        pubs.forEach(pub => {
            const article = document.createElement('article');
            article.className = 'publication-item';

            // Highlight my name
            // Note: Simplistic text replacement. Ideally, use structured author lists.
            let authorHtml = "";
            if (Array.isArray(pub.authors)) {
                authorHtml = pub.authors.map(author => {
                    // Check for loose match
                    const lowerAuthor = author.toLowerCase();
                    if (lowerAuthor.includes("lebiecka") || lowerAuthor.includes("patrycja") || lowerAuthor.includes("książek") || lowerAuthor.includes("ksiazek")) {
                        return `<strong>${author}</strong>`;
                    }
                    return author;
                }).join(', ');
            } else {
                authorHtml = pub.authors; // Fallback if string
            }

            article.innerHTML = `
                <a href="${pub.url || '#'}" target="_blank" class="pub-title">${pub.title}</a>
                <div class="pub-authors">${authorHtml}</div>
                <div class="pub-venue">
                    ${pub.venue} ${pub.year ? `(${pub.year})` : ''}
                </div>
                ${pub.url ? `
                <div class="pub-links">
                    <a href="${pub.url}" target="_blank" class="pub-tag">Paper</a>
                </div>` : ''}
            `;

            pubListContainer.appendChild(article);
        });
    }

    loadPublications();
});
