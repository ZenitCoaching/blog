# Istruzioni per l'agente — Zenit Blog

## Quando si pubblica un nuovo articolo

Ogni volta che viene creato o modificato un file HTML in `blog/` o in `trading/blog/*/`, **devi** eseguire questi passaggi prima di committare:

1. **Aggiornare il blog index**
   ```bash
   python3 scripts/update-blog-index.py
   ```
   Questo sincronizza automaticamente `trading/blog/index.html` con tutti gli articoli presenti nella repo.

2. **Verificare il dominio**
   Tutti i link, i canonical e gli Open Graph devono usare `zenitcoach.com`, **mai** `zenitcoaching.it`.

3. **Committare e pushare**
   Includi sempre sia il nuovo articolo sia l'index aggiornato nello stesso commit.

## Struttura URL

- Articoli in `blog/*.html` → URL pubblico: `/blog/nome-file.html`
- Articoli in `trading/blog/*/index.html` → URL pubblico: `/trading/blog/nome-cartella/`
