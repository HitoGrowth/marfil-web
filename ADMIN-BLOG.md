# Blog de Marfil: panel de administración privado

Los visitantes de la web **solo pueden leer** el blog. Los artículos se escriben desde
`https://marfil.com.mx/admin`, un panel que **solo ven los administradores**.

## Cómo está protegido `/admin`

Hay tres cerraduras independientes. Basta con que una funcione para que nadie más entre.

| Cerradura | Qué hace | Si alguien sin permiso lo intenta |
| --- | --- | --- |
| **1. Cloudflare Access** | Pide el correo y envía un código de un solo uso. Solo acepta los correos de la lista de administradores. | Ve la pantalla de acceso de Cloudflare y no recibe ningún código. |
| **2. Cortafuegos propio** (`functions/admin/_middleware.js`) | Comprueba la firma digital del pase de Access en cada visita. **Falla cerrado**: si Access se desactiva o se configura mal, `/admin` responde *404, no existe*. | 404. El panel ni siquiera se descarga. |
| **3. GitHub** | Solo quien tenga permiso de escritura en el repositorio privado puede guardar cambios. | Aunque viera el panel, no podría iniciar sesión ni publicar. |

Además, `/admin` no aparece enlazado en ningún sitio, no se indexa en Google (`noindex`) y no se guarda en caché.

## Cómo funciona

```
Administrador → marfil.com.mx/admin → Cloudflare Access (correo + código)
             → Sveltia CMS → "Iniciar sesión con GitHub" → escribe y pulsa Guardar
             → GitHub guarda content/blog/<articulo>.json
             → Cloudflare Pages reconstruye la web (1–2 min) con tools/build_pages.py
             → el artículo aparece en /blog, en la portada y en ES / EN / 中文
```

- El español es obligatorio. Si falta el inglés o el chino, la web muestra el texto en español.
- Para ocultar un artículo sin borrarlo, desactiva **Publicado**.
- Las fotos se convierten solas a WebP de 1600 px como máximo.

---

## Puesta en marcha (una sola vez)

Necesitas una cuenta de GitHub (gratuita) y la cuenta de Cloudflare donde ya está la web.
Calcula unos 30–40 minutos.

### Paso 1. Subir el proyecto a un repositorio privado de GitHub

1. En GitHub, crea un repositorio nuevo, por ejemplo `marfil-web`, y márcalo como **Private**.
2. Sube esta carpeta del proyecto: `marfil/`, `content/`, `functions/`, `tools/`, `marca/`, `PRODUCT.md`, `ADMIN-BLOG.md` y `.gitignore`. Puedes hacerlo con GitHub Desktop o desde la terminal:

```bash
git init -b main && git add . && git commit -m "Web de Marfil con blog" && git remote add origin https://github.com/USUARIO/marfil-web.git && git push -u origin main
```

### Paso 2. Crear el proyecto de Cloudflare Pages conectado a GitHub

Los proyectos creados subiendo un ZIP no se pueden conectar a GitHub, así que hay que crear uno nuevo.

1. Cloudflare → **Workers & Pages** → **Create** → **Pages** → **Connect to Git** → elige `marfil-web`.
2. Configuración de compilación:
   - **Framework preset:** None
   - **Build command:** `python3 tools/build_pages.py`
   - **Build output directory:** `marfil`
   - **Root directory:** déjalo vacío
3. **Save and Deploy**. Cuando funcione, mueve el dominio `marfil.com.mx` del proyecto antiguo al nuevo (**Custom domains**).

> Hasta que completes los pasos 3 y 4, `/admin` responde *404* para todo el mundo. Es lo esperado: el cortafuegos falla cerrado.

### Paso 3. Cloudflare Access: la lista de administradores

1. Cloudflare → **Zero Trust**. El plan **Free** cubre hasta 50 usuarios. La primera vez te pedirá un nombre de equipo, por ejemplo `marfil`, que da `marfil.cloudflareaccess.com`.
2. **Access → Applications → Add an application → Self-hosted**.
   - **Name:** `Marfil · admin blog`
   - **Session duration:** 24 hours
   - **Destinations / Public hostnames**: añade estas dos, ambas con **path** `admin`:
     - `marfil.com.mx`
     - `NOMBRE-PROYECTO.pages.dev`
   - Las vistas previas (`*.NOMBRE-PROYECTO.pages.dev`) quedan bloqueadas por el cortafuegos, que responde 404. Si además quieres cerrarlas por completo, ve al proyecto de Pages → **Settings → General → Access policy → Enable**.
3. **Policy:** Action **Allow** → Include → **Emails** → escribe los correos de los administradores.
4. **Login methods:** One-time PIN.
5. Guarda. En la ficha de la aplicación copia el **Application Audience (AUD) Tag**.

### Paso 4. Conectar el cortafuegos con Access

En el proyecto de Pages → **Settings → Variables and Secrets**, añade estas variables en **Production** y en **Preview**:

| Variable | Valor |
| --- | --- |
| `ACCESS_TEAM_DOMAIN` | `marfil.cloudflareaccess.com` (tu nombre de equipo) |
| `ACCESS_AUD` | El AUD Tag del paso 3 |
| `ADMIN_EMAILS` | (Opcional, recomendado) los mismos correos separados por comas. Es una lista de seguridad adicional. |

Después vuelve a desplegar: **Deployments → Retry deployment**.

### Paso 5. Inicio de sesión con GitHub dentro del panel

1. Despliega el autenticador oficial con este botón: <https://deploy.workers.cloudflare.com/?url=https://github.com/sveltia/sveltia-cms-auth>. Al terminar tendrás una URL del tipo `https://sveltia-cms-auth.TU-SUBDOMINIO.workers.dev`.
2. En GitHub → **Settings → Developer settings → OAuth Apps → New OAuth App**:
   - **Homepage URL:** `https://marfil.com.mx`
   - **Authorization callback URL:** `https://sveltia-cms-auth.TU-SUBDOMINIO.workers.dev/callback`
   - Pulsa **Generate a new client secret** y copia el **Client ID** y el **Client secret**.
3. En Cloudflare → el Worker `sveltia-cms-auth` → **Settings → Variables**:
   - `GITHUB_CLIENT_ID` = Client ID
   - `GITHUB_CLIENT_SECRET` = Client secret (pulsa **Encrypt**)
   - `ALLOWED_DOMAINS` = `marfil.com.mx, *.pages.dev`
4. Edita `marfil/admin/config.yml` y cambia las dos líneas marcadas con `<-- CAMBIAR`:
   - `repo: USUARIO/marfil-web`
   - `base_url: https://sveltia-cms-auth.TU-SUBDOMINIO.workers.dev`

   Sube el cambio a GitHub.

### Paso 6. Dar acceso a cada administrador

Cada administrador necesita estar en los dos sitios:

1. **Cloudflare Access:** su correo en la política del paso 3 (y en `ADMIN_EMAILS` si la usas).
2. **GitHub:** repositorio → **Settings → Collaborators → Add people** con el rol **Write**.

Para quitarle el acceso a alguien, bórralo de los dos sitios.

### Paso 7. Comprobación final

- **Ventana privada, con un correo que no está en la lista:** al abrir `https://marfil.com.mx/admin` debe aparecer la pantalla de Cloudflare, y el código nunca llega.
- **Con un correo de administrador:** llega el código, se abre el panel y el botón **Iniciar sesión con GitHub** funciona.
- **Publica un artículo de prueba.** Debe aparecer en `/blog` en 1–2 minutos. Después desactiva **Publicado** o bórralo.

---

## Uso diario (para el cliente)

1. Entra en `https://marfil.com.mx/admin`, escribe tu correo y pega el código que recibes.
2. Pulsa **Iniciar sesión con GitHub**. Solo hace falta la primera vez en cada navegador.
3. **Blog → Nuevo.** Rellena el título, la fecha, la imagen de portada, su descripción, el resumen y el texto en **Español**.
4. Si tienes las traducciones, cambia el selector **Español** por **Inglés** o **Chino** y rellénalas.
5. Pulsa **Guardar**. En 1–2 minutos el artículo está publicado.

## Notas técnicas

- **Archivos:** artículos en `content/blog/*.json` (formato i18n `single_file` de Sveltia); imágenes en `marfil/img/blog/`.
- **Generador:** `python3 tools/build_pages.py` crea `marfil/blog/` y el bloque «Blog» de la portada, entre `<!-- blog:start -->` y `<!-- blog:end -->`. Un artículo con errores se salta con un aviso y no rompe la compilación.
- **Seguridad del texto:** el texto de los artículos se convierte a HTML escapando todo; no es posible insertar scripts ni HTML.
- **Versión de Sveltia:** fijada en `marfil/admin/index.html` (0.231.0) y en el esquema de `config.yml`. Para actualizar, cambia el número en los dos sitios y prueba el panel.
- **El ZIP no incluye el panel:** la subida manual por ZIP a Cloudflare no ejecuta el cortafuegos, así que `marfil-cloudflare.zip` se genera **sin** la carpeta `admin/`. El panel solo existe en el despliegue conectado a GitHub.
