# IF Dashboard — Foodology

Dashboard público de In Full para México 🇲🇽, Colombia 🇨🇴 y Perú 🇵🇪.

## URLs (una vez publicado)
```
https://TU_USUARIO.github.io/if-dashboard/mex.html
https://TU_USUARIO.github.io/if-dashboard/col.html
https://TU_USUARIO.github.io/if-dashboard/per.html
```

## Cómo funciona
- GitHub Actions corre **cada miércoles a las 12:00 Colombia** (17:00 UTC)
- El script Python conecta a Redshift con las credenciales guardadas como secrets
- Genera HTML con datos frescos para los 3 países
- GitHub Pages publica los archivos automáticamente
- Las credenciales **nunca se exponen** al browser

## Setup inicial
Ver guía paso a paso en la documentación del proyecto.
