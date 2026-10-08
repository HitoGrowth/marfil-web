#!/usr/bin/env python3
"""Genera las páginas interiores de la web de Marfil (productos, servicios y blog).

Toma de marfil/index.html la cabecera, el pie, el formulario y el sprite de iconos,
para que todas las páginas compartan exactamente el mismo diseño. Los textos de las
páginas viven aquí en ES / EN / ZH y se escriben en marfil/i18n-pages.js.

Los artículos del blog se editan desde el panel /admin (Sveltia CMS), que los guarda en
content/blog/*.json. Este script los convierte en blog/index.html, blog/<slug>.html y en el
bloque "Blog" de la portada (entre los comentarios blog:start y blog:end).

Uso:  python3 tools/build_pages.py
"""
import glob
import html as htmllib
import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'marfil')
CONTENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'content', 'blog')
HOME = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()

# ---------------------------------------------------------------------------
# Textos (es, en, zh). Las claves en ES se escriben en el HTML; EN y ZH en i18n-pages.js
# ---------------------------------------------------------------------------
T = {}


def k(key, es, en, zh):
    T[key] = (es, en, zh)
    return key


# Comunes (también los usa la portada)
k('util.wa', 'Escríbenos por WhatsApp', 'Message us on WhatsApp', '通过 WhatsApp 联系我们')
k('util.mail', 'Escríbenos un correo: contacto@marfil.com.mx', 'Email us: contacto@marfil.com.mx', '发送邮件：contacto@marfil.com.mx')
k('prod.more', 'Más información', 'More information', '了解更多')
k('nav.specs', 'Servicios', 'Services', '服务')
k('hero.title', 'Piel curtida 100% al vegetal', '100% vegetable-tanned leather', '100% 植鞣革')
k('svc.title', 'Servicios', 'Services', '服务')
k('svc.lead', 'Realizamos procesos intermedios que acercan nuestras pieles al producto final que necesita cada cliente.',
  'We carry out intermediate processes that bring our leather closer to the final product each client needs.',
  '我们提供中间加工服务，让皮革更贴近每位客户所需的最终产品。')
k('svc.1t', 'Tiras para cinturón', 'Belt straps', '腰带条')
k('svc.2t', 'Suajado', 'Die cutting', '冲切')

k('crumb.home', 'Inicio', 'Home', '首页')
k('crumb.products', 'Productos', 'Products', '产品')
k('crumb.services', 'Servicios', 'Services', '服务')
k('crumb.label', 'Ruta de navegación', 'Breadcrumb', '导航路径')
k('side.title', 'Categorías', 'Categories', '分类')
k('side.use', 'Uso final', 'End use', '最终用途')
k('cat.pieces', 'Piezas recomendadas', 'Recommended pieces', '推荐部位')
k('cat.quote', 'Cotizar esta pieza', 'Quote this piece', '询价此部位')
k('cat.specs', 'Especificaciones', 'Specifications', '规格')
k('cat.uses', 'Usos', 'Uses', '用途')
k('cat.related', 'Otros productos', 'Other products', '其他产品')
k('cat.othersvc', 'Otros servicios y productos', 'Other services and products', '其他服务与产品')
k('cat.ask', 'Grosores, selecciones y acabados a medida: consúltalos con un asesor.',
  'Thicknesses, grades and finishes to order: ask an advisor.',
  '厚度、等级与表面处理可按需定制，请咨询顾问。')
k('cat.see', 'Ver servicio', 'See service', '查看服务')
k('iron.title', 'Equivalencia de grosor', 'Thickness equivalence', '厚度换算')
k('iron.mm', 'Milímetros (aprox.)', 'Millimetres (approx.)', '毫米（约）')
k('iron.note', '1 iron = 1/48 de pulgada ≈ 0.53 mm', '1 iron = 1/48 inch ≈ 0.53 mm', '1 iron = 1/48 英寸 ≈ 0.53 毫米')
k('how.title', 'Cómo trabajamos', 'How it works', '合作流程')
k('specs.thick', 'Grosor', 'Thickness', '厚度')
k('specs.thick1', '3.5 a 6 mm (7–11 Iron) o 3.5 a 5.5 mm', '3.5 to 6 mm (7–11 Iron) or 3.5 to 5.5 mm', '3.5 至 6 毫米（7–11 Iron）或 3.5 至 5.5 毫米')
k('specs.press', 'Planchado', 'Pressing', '压实度')
k('specs.press1', 'Sin planchar, suave, medio o firme', 'Unpressed, soft, medium or firm', '未压、软、中、硬')
k('specs.finish', 'Acabado', 'Finish', '表面处理')
k('specs.finish1', 'Pulida, no pulida o acabada', 'Polished, unpolished or finished', '抛光、未抛光或涂饰')
k('specs.grades', 'Selecciones', 'Grades', '等级')
k('specs.grades1', 'TR1, TR2, TR3 y TR4', 'TR1, TR2, TR3 and TR4', 'TR1、TR2、TR3 及 TR4')
k('specs.thick2', '2 a 5 mm', '2 to 5 mm', '2 至 5 毫米')
k('specs.color', 'Color', 'Colour', '颜色')
k('specs.color1', 'Natural o colores base de Marfil', 'Natural or Marfil base colours', '原色或 Marfil 基础色')
k('pg.grades3', 'TR1, TR2 y TR3', 'TR1, TR2 and TR3', 'TR1、TR2 及 TR3')

# Piezas
k('pc.centro', 'Centro Suela', 'Sole Bend (Centro Suela)', '中心鞋底革（Centro Suela）')
k('pc.delantero', 'Delantero Suela', 'Sole Shoulder (Delantero Suela)', '肩部鞋底革（Delantero Suela）')
k('pc.sillero', 'Sillero', 'Harness Leather (Sillero)', '马鞍革（Sillero）')
k('pc.crupon', 'Crupón Sillero / Doble Crupón Sillero', 'Harness Bend / Double Harness Bend', '马鞍革臀背部 / 双臀背部')
k('pc.lados', 'Lados', 'Sides', '侧边革')
k('pc.suajada', 'Suela suajada', 'Die-cut soles', '冲切鞋底')
k('pc.tira', 'Tira para cinturón', 'Belt strap', '腰带条')
k('pcm.suela', 'Línea suela · 3.5–6 mm', 'Sole line · 3.5–6 mm', '鞋底革系列 · 3.5–6 毫米')
k('pcm.sillero', 'Línea sillero', 'Harness line', '马鞍革系列')
k('pcm.lados', 'Piezas de lado', 'Side pieces', '侧边部位')
k('pcm.suaj', 'Servicio de suajado · TR1–TR4', 'Die-cutting service · TR1–TR4', '冲切服务 · TR1–TR4')
k('pcm.tiras', 'Corte de tira · 2–5 mm', 'Strap cutting · 2–5 mm', '裁条 · 2–5 毫米')

PIECES = {
    'centro':    dict(name='pc.centro', meta='pcm.suela', img='CentroOrion.webp', w=1080, h=721),
    'delantero': dict(name='pc.delantero', meta='pcm.suela', img='DelanteroOrion.webp', w=1080, h=721),
    'sillero':   dict(name='pc.sillero', meta='pcm.sillero', img='Sillero_natural.jpg', w=1536, h=1024),
    'crupon':    dict(name='pc.crupon', meta='pcm.sillero', img='CruponOrion.webp', w=1080, h=721),
    'lados':     dict(name='pc.lados', meta='pcm.lados', img='LadoOrion.webp', w=1080, h=720),
    'suajada':   dict(name='pc.suajada', meta='pcm.suaj', img='suela_optimizada_web.webp', w=1024, h=1024, photo=True),
    'tira':      dict(name='pc.tira', meta='pcm.tiras', img='IMG_3737_compressed.jpg', w=1436, h=2048, photo=True),
}

# Especificaciones reutilizables (valores tomados de marfil.com.mx)
SPEC_SUELA = [('specs.thick', 'specs.thick1'), ('specs.press', 'specs.press1'),
              ('specs.finish', 'specs.finish1'), ('specs.grades', 'specs.grades1')]
SPEC_TIRAS = [('specs.thick', 'specs.thick2'), ('specs.grades', 'pg.grades3'), ('specs.color', 'specs.color1')]
IRONS = [(7, '3.7'), (8, '4.2'), (9, '4.8'), (10, '5.3'), (11, '5.8')]

# ---------------------------------------------------------------------------
# Páginas de producto (como las páginas de categoría de Wyny, con textos propios)
# ---------------------------------------------------------------------------
PRODUCTS = [
    dict(slug='calzado', ind='calzado', title='prod.1t',
         meta=k('p.calz.meta', 'Piel para calzado: suela 100% curtida al vegetal | Marfil Tannery',
                'Leather for footwear: 100% vegetable-tanned sole leather | Marfil Tannery',
                '鞋履用皮革：100% 植鞣鞋底革 | Marfil Tannery'),
         lead=k('p.calz.lead', 'Piel 100% curtida al vegetal para suela, entresuela, planta y tacón.',
                '100% vegetable-tanned leather for outsoles, midsoles, insoles and heels.',
                '100% 植鞣革，适用于大底、中底、内底及鞋跟。'),
         intro=k('p.calz.intro',
                 'Curtimos en pila y tambor con taninos naturales para lograr una suela firme, de fibra compacta y resistente al desgaste: la base del calzado premium, artesanal y de la bota vaquera. Te ayudamos a elegir la pieza, el grosor y el planchado que necesita tu producción.',
                 'We tan in pits and drums with natural tannins to achieve a firm, compact-fibred sole leather that resists wear: the foundation of premium, handcrafted and western footwear. We help you choose the piece, thickness and pressing your production needs.',
                 '我们以天然单宁进行池鞣与转鼓鞣制，打造坚实、纤维紧密且耐磨的鞋底革：这是高端鞋、手工鞋与西部牛仔靴的基础。我们协助您选择适合生产的部位、厚度与压实度。'),
         uses=k('p.calz.uses', 'Suela, entresuela, planta, tacón y taloneras para zapato y bota vaquera.',
                'Outsoles, midsoles, insoles, heels and heel counters for shoes and western boots.',
                '适用于正装鞋与西部牛仔靴的大底、中底、内底、鞋跟及后跟。'),
         pieces=['centro', 'delantero', 'suajada'], specs=SPEC_SUELA, irons=True,
         svc=('suajado', 'svc.2t')),
    dict(slug='marroquineria', ind='marroquineria', title='prod.2t',
         meta=k('p.marr.meta', 'Piel vegetal para marroquinería | Marfil Tannery',
                'Vegetable-tanned leather for leather goods | Marfil Tannery',
                '皮具用植鞣革 | Marfil Tannery'),
         lead=k('p.marr.lead', 'Piel curtida al vegetal para bolsas, carteras y accesorios.',
                'Vegetable-tanned leather for handbags, wallets and accessories.',
                '适用于手袋、钱包及配饰的植鞣革。'),
         intro=k('p.marr.intro',
                 'El curtido vegetal da a cada pieza un tacto natural y una pátina que se enriquece con el uso, ideal para marroquinería con carácter. Seleccionamos la parte de la piel según el artículo: piezas firmes para dar estructura y zonas más flexibles y suaves para forros y detalles.',
                 'Vegetable tanning gives every piece a natural hand and a patina that deepens with use, ideal for leather goods with character. We select the part of the hide for each article: firm pieces for structure and softer, more flexible areas for linings and details.',
                 '植物鞣制赋予每件皮革自然的手感，以及随使用愈发丰富的光泽，非常适合富有个性的皮具。我们按产品挑选皮革部位：坚实部位用于塑形，较柔软的部位用于内衬与细节。'),
         uses=k('p.marr.uses', 'Bolsas, carteras, forros y accesorios de piel.',
                'Handbags, wallets, linings and leather accessories.',
                '手袋、钱包、内衬及皮革配饰。'),
         pieces=['sillero', 'lados'], specs=None, irons=False, svc=None),
    dict(slug='tiras-para-cinturon', ind='tiras', title='prod.3t',
         meta=k('p.tira.meta', 'Tiras para cinturón de cuero 100% vegetal | Marfil Tannery',
                '100% vegetable-tanned belt straps | Marfil Tannery',
                '100% 植鞣腰带条 | Marfil Tannery'),
         lead=k('p.tira.lead', 'Sillero y crupón sillero 100% vegetal, en piel o cortados en tira.',
                '100% vegetable-tanned harness leather and harness bend, as hides or cut into straps.',
                '100% 植鞣马鞍革与臀背部革，可供整张皮或裁条。'),
         intro=k('p.tira.intro',
                 'Para un cinturón que dure años trabajamos con sillero y crupón sillero (culata) 100% vegetal: piezas firmes y resistentes a la tensión. Te entregamos la piel o la tira ya cortada, en natural o en los colores base de Marfil.',
                 'For a belt that lasts for years we work with 100% vegetable-tanned harness leather and harness bend: firm pieces that resist tension. We supply the hide or the strap already cut, natural or in Marfil base colours.',
                 '为打造经久耐用的腰带，我们选用 100% 植鞣马鞍革与臀背部革：坚实且耐拉伸。我们可提供整张皮或已裁好的皮条，原色或 Marfil 基础色。'),
         uses=k('p.tira.uses', 'Cinturones, correas, arneses y riendas.',
                'Belts, straps, harnesses and reins.',
                '腰带、皮带、挽具及缰绳。'),
         pieces=['sillero', 'crupon', 'tira'], specs=SPEC_TIRAS, irons=False,
         svc=('tiras-para-cinturon', 'svc.1t')),
    dict(slug='sillas-de-montar', ind='silleria', title='prod.4t',
         meta=k('p.sill.meta', 'Piel para sillas de montar y talabartería | Marfil Tannery',
                'Leather for saddlery and tack | Marfil Tannery',
                '马鞍与马具用皮革 | Marfil Tannery'),
         lead=k('p.sill.lead', 'Piezas grandes y firmes para sillas de montar y talabartería.',
                'Large, firm pieces for saddles and tack.',
                '适用于马鞍与马具的大面积坚实皮料。'),
         intro=k('p.sill.intro',
                 'Para cualquier tipo de silla de montar y accesorio de talabartería seleccionamos piezas de gran tamaño, con buen aprovechamiento y la firmeza que pide el cincelado. El curtido vegetal permite trabajar, grabar y moldear la piel con precisión.',
                 'For any kind of saddle and tack accessory we select large pieces with good yield and the firmness that carving requires. Vegetable tanning lets you tool, stamp and mould the leather with precision.',
                 '我们为各类马鞍及马具配件挑选面积大、利用率高且坚实、适合雕花的皮料。植物鞣制让皮革便于精准加工、压纹与塑形。'),
         uses=k('p.sill.uses', 'Sillas de montar, monturas cinceladas, arneses, riendas y accesorios de talabartería.',
                'Saddles, carved saddlery, harnesses, reins and tack accessories.',
                '马鞍、雕花马具、挽具、缰绳及马具配件。'),
         pieces=['sillero', 'crupon', 'lados'], specs=None, irons=False, svc=None),
]

# ---------------------------------------------------------------------------
# Páginas de servicio (contenido de marfil.com.mx/servicios)
# ---------------------------------------------------------------------------
SERVICES = [
    dict(slug='tiras-para-cinturon', ind='tiras', crumb='svc.1t', img='Diseno-sin-titulo-2-scaled-e1770997071546.jpg', iw=1707, ih=1438,
         img2='IMG_3737_compressed.jpg', i2w=1436, i2h=2048,
         meta=k('s.tira.meta', 'Corte de tiras para cinturón | Marfil Tannery', 'Belt strap cutting | Marfil Tannery', '腰带条裁切 | Marfil Tannery'),
         title=k('s.tira.title', 'Corte de tiras para cinturón', 'Belt strap cutting', '腰带条裁切'),
         lead=k('s.tira.lead', 'Tiras de cuero 100% vegetal, cortadas a la medida de tu producción.',
                '100% vegetable-tanned leather straps, cut to fit your production.',
                '100% 植鞣皮条，按您的生产需求裁切。'),
         body=[k('s.tira.b1', 'Cortamos tiras de cuero vegetal de alta calidad para fabricar cinturones duraderos y con estilo. Trabajamos con sillero 100% vegetal y crupón sillero (culata), las pieles que mejor responden en un cinturón.',
                 'We cut high-quality vegetable-tanned leather straps for durable, stylish belts. We work with 100% vegetable-tanned harness leather and harness bend, the hides that perform best in a belt.',
                 '我们裁切高品质植鞣皮条，用于制作耐用且有型的腰带。我们选用 100% 植鞣马鞍革与臀背部革，这是最适合腰带的皮料。'),
               k('s.tira.b2', 'Nos adaptamos a las necesidades de cada cliente: grosor, selección y color se definen contigo antes de cortar.',
                 'We adapt to each client’s needs: thickness, grade and colour are agreed with you before cutting.',
                 '我们根据每位客户的需求灵活调整：厚度、等级与颜色均在裁切前与您确认。')],
         specs=SPEC_TIRAS, irons=False,
         how=[k('s.tira.h1', 'Nos cuentas grosor, ancho, color y volumen.', 'You tell us thickness, width, colour and volume.', '告诉我们厚度、宽度、颜色与用量。'),
              k('s.tira.h2', 'Seleccionamos la piel: sillero o crupón sillero.', 'We select the hide: harness leather or harness bend.', '我们挑选皮料：马鞍革或臀背部革。'),
              k('s.tira.h3', 'Cortamos y te entregamos las tiras listas para producción.', 'We cut and deliver the straps ready for production.', '裁切完成后，交付可直接投产的皮条。')],
         other=('suajado', 'svc.2t'), product=('tiras-para-cinturon', 'prod.3t')),
    dict(slug='suajado', ind='calzado', crumb='svc.2t', img='Diseno-sin-titulo-2-1.jpg', iw=2560, ih=1800,
         img2='suela_optimizada_web.webp', i2w=1024, i2h=1024,
         meta=k('s.suaj.meta', 'Suelas suajadas de cuero 100% vegetal | Marfil Tannery', '100% vegetable-tanned die-cut soles | Marfil Tannery', '100% 植鞣冲切鞋底 | Marfil Tannery'),
         title=k('s.suaj.title', 'Suelas suajadas', 'Die-cut soles', '冲切鞋底'),
         lead=k('s.suaj.lead', 'Suelas de cuero 100% vegetal, cortadas con precisión según tus especificaciones.',
                '100% vegetable-tanned leather soles, precision-cut to your specifications.',
                '100% 植鞣皮革鞋底，按您的规格精准裁切。'),
         body=[k('s.suaj.b1', 'Entregamos suelas suajadas listas para integrarse a tu producción. Para calzado artesanal y de alta calidad, ofrecen durabilidad, confort y un aspecto natural.',
                 'We deliver die-cut soles ready to go straight into your production. For handcrafted and high-quality footwear, they offer durability, comfort and a natural look.',
                 '我们交付可直接投入生产的冲切鞋底。适用于手工及高品质鞋履，兼具耐用、舒适与自然外观。'),
               k('s.suaj.b2', 'Cortamos suela, tapa o tacón y taloneras, ideales para zapato o bota vaquera. Nos adaptamos a tus necesidades.',
                 'We cut soles, top lifts or heels and heel counters, ideal for shoes or western boots. We adapt to your needs.',
                 '我们裁切鞋底、鞋跟面皮或鞋跟及后跟，适用于正装鞋或西部牛仔靴，并可按需调整。')],
         specs=SPEC_SUELA, irons=True,
         how=[k('s.suaj.h1', 'Envíanos tus moldes o especificaciones.', 'Send us your patterns or specifications.', '发送您的模板或规格要求。'),
              k('s.suaj.h2', 'Definimos grosor, planchado, acabado y selección.', 'We define thickness, pressing, finish and grade.', '确定厚度、压实度、表面处理与等级。'),
              k('s.suaj.h3', 'Suajamos y entregamos las suelas listas para producción.', 'We die-cut and deliver the soles ready for production.', '冲切完成后，交付可直接投产的鞋底。')],
         other=('tiras-para-cinturon', 'svc.1t'), product=('calzado', 'prod.1t')),
]

# ---------------------------------------------------------------------------
# Piezas compartidas con la portada
# ---------------------------------------------------------------------------
DICT_ES = {}
for m in re.finditer(r'data-i18n="([^"]+)">([^<]*)<', HOME):
    DICT_ES.setdefault(m.group(1), m.group(2))


def es(key):
    if key in T:
        return T[key][0]
    if key in DICT_ES:
        return DICT_ES[key]
    raise KeyError(key)


def esc(text):
    return htmllib.escape(text or '', quote=True)


def js_json(obj):
    """JSON seguro para incrustar dentro de <script>."""
    return (json.dumps(obj, ensure_ascii=False).replace('</', '<\\/')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def grab(start, end, src=HOME):
    a = src.index(start)
    b = src.index(end, a) + len(end)
    return src[a:b]


SPRITE = grab('<svg class="sprite"', '</symbol>\n</svg>')
UTILITY = grab('<div class="utility">', '</div>\n</div>')
HEADER = grab('<header class="nav"', '</header>')
FOOTER = grab('<footer class="footer', '</footer>')
CONTACT = grab('<section class="section section--mist" id="contacto">', '</section>')
STICKY = grab('<a class="sticky-cta', '</a>')
PRODUCT_ICONS = {}
for slug, ico in zip(['calzado', 'marroquineria', 'tiras-para-cinturon', 'sillas-de-montar'],
                     re.findall(r'(<span class="pcard__badge".*?</svg>\s*</span>)', HOME, re.S)):
    PRODUCT_ICONS[slug] = ico


def relink(html, depth):
    """Ajusta rutas de la portada para una página a `depth` carpetas de profundidad."""
    up = '../' * depth
    html = re.sub(r'href="#(productos|servicios|eco|nosotros)"', lambda m: f'href="{up}index.html#{m.group(1)}"', html)
    html = html.replace('href="#top"', f'href="{up}index.html"')
    html = re.sub(r'(src|href)="(img/|productos/|servicios/|blog/)', lambda m: f'{m.group(1)}="{up}{m.group(2)}', html)
    return html


def contact_block(industry):
    c = CONTACT
    c = c.replace('<option value="%s" ' % industry, '<option value="%s" selected ' % industry)
    return c


def head(meta_key, depth, title=None, desc_key=None, desc=None):
    up = '../' * depth
    h = HOME[:HOME.index('<body>')]
    h = re.sub(r'<title data-i18n="meta.title">[^<]*</title>', lambda m: f'<title data-i18n="{meta_key}">{esc(title if title is not None else es(meta_key))}</title>', h)
    if desc_key:
        h = re.sub(r'<meta name="description" data-i18n-attr="content:meta.desc" content="[^"]*">',
                   lambda m: f'<meta name="description" data-i18n-attr="content:{desc_key}" content="{esc(desc)}">', h)
    h = h.replace('href="styles.css"', f'href="{up}styles.css"').replace('href="img/', f'href="{up}img/')
    h = re.sub(r'<link rel="alternate"[^>]*>\n', '', h)
    return h


def page(meta_key, main, industry, depth=1, title=None, desc_key=None, desc=None, local=None, nav_current=None):
    up = '../' * depth
    header = relink(HEADER, depth)
    if nav_current:
        header = header.replace(f'href="{up}{nav_current}"', f'href="{up}{nav_current}" aria-current="page"', 1)
    local_js = f'<script>window.MARFIL_LOCAL = {js_json(local)};</script>\n' if local else ''
    return (head(meta_key, depth, title, desc_key, desc) + '<body class="page-inner">\n' + SPRITE + '\n'
            + '<a class="skip" href="#contenido" data-i18n="skip">Saltar al contenido</a>\n\n'
            + relink(UTILITY, depth) + '\n\n' + header + '\n\n<main id="contenido">\n'
            + main + '\n' + relink(contact_block(industry), depth) + '\n\n</main>\n\n'
            + relink(FOOTER, depth) + '\n\n' + STICKY + '\n\n'
            + local_js + f'<script src="{up}i18n-pages.js"></script>\n<script src="{up}i18n.js"></script>\n<script src="{up}script.js"></script>\n</body>\n</html>\n')


def tx(key, tag='span', cls=None, extra=''):
    c = f' class="{cls}"' if cls else ''
    return f'<{tag}{c} data-i18n="{key}"{extra}>{es(key)}</{tag}>'


def crumbs(items):
    parts = []
    for href, key in items:
        if href:
            parts.append(f'<a href="{href}" data-i18n="{key}">{es(key)}</a>')
        else:
            parts.append(f'<span aria-current="page" data-i18n="{key}">{es(key)}</span>')
    return ('<nav class="crumbs" data-i18n-attr="aria-label:crumb.label" aria-label="%s">' % es('crumb.label')
            + '<span class="crumbs__sep" aria-hidden="true">/</span>'.join(parts) + '</nav>')


def spec_list(specs):
    rows = ''.join(f'<div><dt data-i18n="{a}">{es(a)}</dt><dd data-i18n="{b}">{es(b)}</dd></div>' for a, b in specs)
    return f'<dl class="spec-list">{rows}</dl>'


def iron_table():
    rows = ''.join(f'<tr><td>{i}</td><td>{mm}</td></tr>' for i, mm in IRONS)
    return (f'<div class="iron"><h3 class="iron__title" data-i18n="iron.title">{es("iron.title")}</h3>'
            f'<table><thead><tr><th scope="col">Iron</th><th scope="col" data-i18n="iron.mm">{es("iron.mm")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table><p class="iron__note" data-i18n="iron.note">{es("iron.note")}</p></div>')


def sidebar(current):
    links = ''
    for p in PRODUCTS:
        cur = ' aria-current="page"' if p['slug'] == current else ''
        links += f'<li><a href="../productos/{p["slug"]}.html"{cur} data-i18n="{p["title"]}">{es(p["title"])}</a></li>'
    svcs = ''
    for s in SERVICES:
        cur = ' aria-current="page"' if ('svc:' + s['slug']) == current else ''
        svcs += f'<li><a href="../servicios/{s["slug"]}.html"{cur} data-i18n="{s["crumb"]}">{es(s["crumb"])}</a></li>'
    return (f'<aside class="side"><p class="side__title" data-i18n="side.title">{es("side.title")}</p>'
            f'<p class="side__group" data-i18n="side.use">{es("side.use")}</p><ul>{links}</ul>'
            f'<p class="side__group" data-i18n="crumb.services">{es("crumb.services")}</p><ul>{svcs}</ul></aside>')


def piece_card(pk, industry):
    p = PIECES[pk]
    cls = 'piece__img piece__img--photo' if p.get('photo') else 'piece__img'
    return (f'<li class="piece reveal"><div class="{cls}"><img src="../img/{p["img"]}" alt="" width="{p["w"]}" height="{p["h"]}" loading="lazy"></div>'
            f'<div class="piece__body"><h3 data-i18n="{p["name"]}">{es(p["name"])}</h3>'
            f'<p class="piece__meta" data-i18n="{p["meta"]}">{es(p["meta"])}</p>'
            f'<a class="btn btn--ghost piece__btn" href="#contacto" data-industria="{industry}" data-pieza="{es(p["name"])}" data-i18n="cat.quote">{es("cat.quote")}</a></div></li>')


def mini_card(href, key, ico=''):
    return (f'<li><a class="mini" href="{href}">{ico}<span class="mini__title" data-i18n="{key}">{es(key)}</span>'
            f'<span class="mini__more"><span data-i18n="prod.more">{es("prod.more")}</span> <span class="arrow" aria-hidden="true">→</span></span></a></li>')


def product_page(p):
    specs = ''
    if p['specs']:
        specs = f'<div class="catalog__specs reveal"><h2 class="h-sub" data-i18n="cat.specs">{es("cat.specs")}</h2>{spec_list(p["specs"])}'
        if p['irons']:
            specs += iron_table()
        specs += '</div>'
    else:
        specs = (f'<div class="catalog__specs reveal"><h2 class="h-sub" data-i18n="cat.specs">{es("cat.specs")}</h2>'
                 f'<p class="catalog__ask" data-i18n="cat.ask">{es("cat.ask")}</p></div>')
    svc = ''
    if p['svc']:
        slug, key = p['svc']
        svc = (f'<a class="link" href="../servicios/{slug}.html"><span><span data-i18n="cat.see">{es("cat.see")}</span>: '
               f'<span data-i18n="{key}">{es(key)}</span></span> <span class="arrow" aria-hidden="true">→</span></a>')
    related = ''.join(mini_card(f'../productos/{o["slug"]}.html', o['title'], PRODUCT_ICONS[o['slug']].replace('pcard__badge', 'mini__badge'))
                      for o in PRODUCTS if o['slug'] != p['slug'])
    pieces = ''.join(piece_card(pk, p['ind']) for pk in p['pieces'])
    main = f'''
<section class="page-hero">
  <div class="wrap">
    {crumbs([('../index.html', 'crumb.home'), ('../index.html#productos', 'crumb.products'), (None, p['title'])])}
    <div class="page-hero__row">
      {PRODUCT_ICONS[p['slug']].replace('pcard__badge', 'page-hero__badge')}
      <div>
        <h1 data-i18n="{p['title']}">{es(p['title'])}</h1>
        <p class="page-hero__lead" data-i18n="{p['lead']}">{es(p['lead'])}</p>
      </div>
    </div>
  </div>
</section>

<section class="section catalog-section">
  <div class="wrap catalog">
    {sidebar(p['slug'])}
    <div class="catalog__main">
      <div class="catalog__intro reveal">
        <p data-i18n="{p['intro']}">{es(p['intro'])}</p>
        <p class="catalog__uses"><strong data-i18n="cat.uses">{es('cat.uses')}</strong> <span data-i18n="{p['uses']}">{es(p['uses'])}</span></p>
        {svc}
      </div>
      <h2 class="h-sub" data-i18n="cat.pieces">{es('cat.pieces')}</h2>
      <ul class="pieces">{pieces}</ul>
      {specs}
    </div>
  </div>
</section>

<section class="section section--plaster related">
  <div class="wrap">
    <h2 class="h-sub" data-i18n="cat.related">{es('cat.related')}</h2>
    <ul class="minis">{related}</ul>
  </div>
</section>
'''
    return page(p['meta'], main, p['ind'])


def service_page(s):
    body = ''.join(f'<p data-i18n="{b}">{es(b)}</p>' for b in s['body'])
    steps = ''.join(f'<li><span class="steps__n" aria-hidden="true">{i}</span><p data-i18n="{h}">{es(h)}</p></li>' for i, h in enumerate(s['how'], 1))
    specs = spec_list(s['specs']) + (iron_table() if s['irons'] else '')
    oslug, okey = s['other']
    pslug, pkey = s['product']
    svc_icon = {'tiras-para-cinturon': 'tiras-para-cinturon', 'suajado': 'calzado'}
    minis = (mini_card(f'../servicios/{oslug}.html', okey, PRODUCT_ICONS[svc_icon[oslug]].replace('pcard__badge', 'mini__badge'))
             + mini_card(f'../productos/{pslug}.html', pkey, PRODUCT_ICONS[pslug].replace('pcard__badge', 'mini__badge')))
    main = f'''
<section class="page-hero page-hero--image">
  <img class="page-hero__img" src="../img/{s['img']}" alt="" width="{s['iw']}" height="{s['ih']}" fetchpriority="high">
  <div class="wrap">
    {crumbs([('../index.html', 'crumb.home'), ('../index.html#servicios', 'crumb.services'), (None, s['crumb'])])}
    <h1 data-i18n="{s['title']}">{es(s['title'])}</h1>
    <p class="page-hero__lead" data-i18n="{s['lead']}">{es(s['lead'])}</p>
    <a class="btn btn--primary" href="#contacto" data-i18n="cta.quote">{es('cta.quote')}</a>
  </div>
</section>

<section class="section catalog-section">
  <div class="wrap catalog">
    {sidebar('svc:' + s['slug'])}
    <div class="catalog__main">
      <div class="svc-detail">
        <div class="svc-detail__text reveal">{body}</div>
        <figure class="svc-detail__img reveal"><img src="../img/{s['img2']}" alt="" width="{s['i2w']}" height="{s['i2h']}" loading="lazy"></figure>
      </div>
      <div class="catalog__specs reveal"><h2 class="h-sub" data-i18n="cat.specs">{es('cat.specs')}</h2>{specs}</div>
      <div class="how reveal">
        <h2 class="h-sub" data-i18n="how.title">{es('how.title')}</h2>
        <ol class="steps">{steps}</ol>
      </div>
    </div>
  </div>
</section>

<section class="section section--plaster related">
  <div class="wrap">
    <h2 class="h-sub" data-i18n="cat.othersvc">{es('cat.othersvc')}</h2>
    <ul class="minis minis--2">{minis}</ul>
  </div>
</section>
'''
    return page(s['meta'], main, s['ind'])


# ---------------------------------------------------------------------------
# Blog: content/blog/*.json (Sveltia CMS, i18n single_file) → páginas estáticas
# ---------------------------------------------------------------------------
k('nav.blog', 'Blog', 'Blog', '博客')
k('crumb.blog', 'Blog', 'Blog', '博客')
k('blog.h1', 'Blog', 'Blog', '博客')
k('blog.title', 'Desde la tenería.', 'From the tannery.', '来自制革厂。')
k('blog.lead', 'Procesos, materiales y novedades de Marfil, contados por quienes trabajamos la piel.',
  'Processes, materials and news from Marfil, told by the people who work the leather.',
  '由亲手制革的我们，讲述 Marfil 的工艺、材料与动态。')
k('blog.all', 'Ver todos los artículos', 'See all articles', '查看全部文章')
k('blog.read', 'Leer artículo', 'Read article', '阅读文章')
k('blog.back', 'Volver al blog', 'Back to the blog', '返回博客')
k('blog.more', 'Más artículos', 'More articles', '更多文章')
k('blog.empty', 'Muy pronto publicaremos nuestros primeros artículos.', 'Our first articles are coming soon.', '首批文章即将发布。')
k('meta.blog', 'Blog | Marfil Tannery', 'Blog | Marfil Tannery', '博客 | Marfil Tannery')
k('meta.blogdesc', 'Artículos sobre curtido vegetal, procesos y novedades de Marfil Tannery, tenería en León, Guanajuato.',
  'Articles on vegetable tanning, processes and news from Marfil Tannery, a tannery in León, Guanajuato.',
  '关于植物鞣制、工艺以及 Marfil Tannery（墨西哥瓜纳华托州莱昂制革厂）动态的文章。')

LANGS = ['es', 'en', 'zh']
HTML_LANG = {'es': 'es', 'en': 'en', 'zh': 'zh-Hans'}
MONTHS_ES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
             'septiembre', 'octubre', 'noviembre', 'diciembre']
SLUG_RE = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
HOME_POSTS = 3


def warn(msg):
    print('AVISO blog:', msg)


def asset(path, up):
    """Rutas de imagen del CMS (/img/blog/x.webp) → relativas a la página."""
    path = (path or '').strip()
    if re.match(r'https://', path, re.I):
        return path
    if not path or re.match(r'[a-z][a-z0-9+.-]*:', path, re.I) or path.startswith('//') or '..' in path:
        return ''
    return up + path.lstrip('/')


def safe_href(url, up):
    url = (url or '').strip()
    if re.match(r'(https?:|mailto:|tel:)', url, re.I) or url.startswith('#'):
        return url
    if re.match(r'[a-z][a-z0-9+.-]*:', url, re.I) or url.startswith('//'):
        return ''  # javascript:, data:, etc.
    return up + url.lstrip('/') if url.startswith('/') else url


# --- Markdown → HTML (el subconjunto que produce el editor de Sveltia) -------
# Todo el texto se escapa: un artículo no puede inyectar HTML ni scripts en la web.
IMG_MD = r'!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+"([^"]*)")?\s*\)'
LINK_MD = r'\[([^\]]+)\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)'


def md_inline(text, up):
    keep = []

    def stash(html):
        keep.append(html)
        return '\x00%d\x00' % (len(keep) - 1)

    def image(m):
        src = asset(m.group(2), up)
        return stash('<img src="%s" alt="%s" loading="lazy">' % (esc(src), esc(m.group(1)))) if src else ''

    def link(m):
        href = safe_href(m.group(2), up)
        label = md_inline(m.group(1), up)
        if not href:
            return stash(label)
        ext = ' target="_blank" rel="noopener"' if re.match(r'https?:', href, re.I) else ''
        return stash('<a href="%s"%s>%s</a>' % (esc(href), ext, label))

    text = re.sub(r'\\([\\`*_{}\[\]()#+\-.!>~|<])', lambda m: stash(esc(m.group(1))), text)
    text = re.sub(r'`([^`]+)`', lambda m: stash('<code>%s</code>' % esc(m.group(1))), text)
    text = re.sub(IMG_MD, image, text)
    text = re.sub(LINK_MD, link, text)
    text = re.sub(r'<(https?://[^>\s]+)>',
                  lambda m: stash('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(m.group(1)), esc(m.group(1)))), text)
    text = esc(text)
    text = re.sub(r'\*\*(.+?)\*\*|__(.+?)__', lambda m: '<strong>%s</strong>' % (m.group(1) or m.group(2)), text)
    text = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])|(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])',
                  lambda m: '<em>%s</em>' % (m.group(1) or m.group(2)), text)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    while '\x00' in text:  # restaura marcadores (también los anidados)
        text = re.sub(r'\x00(\d+)\x00', lambda m: keep[int(m.group(1))], text)
    return text


LIST_RE = re.compile(r'^( *)([-*+]|\d+[.)])\s+(.*)$')


def md_to_html(md, up):
    lines = (md or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append('<p>' + '<br>'.join(md_inline(l.strip(), up) for l in para) + '</p>')
            del para[:]

    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if not st:
            flush(); i += 1; continue
        if st.startswith('```'):
            flush(); code = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            out.append('<pre><code>' + esc('\n'.join(code)) + '</code></pre>'); i += 1; continue
        m = re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', st)
        if m:
            flush()
            level = min(max(len(m.group(1)), 2), 4)  # el título del artículo es el único h1
            out.append('<h%d>%s</h%d>' % (level, md_inline(m.group(2), up), level)); i += 1; continue
        if re.fullmatch(r'(\*\s*){3,}|(-\s*){3,}|(_\s*){3,}', st):
            flush(); out.append('<hr>'); i += 1; continue
        if st.startswith('>'):
            flush(); quote = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote.append(re.sub(r'^\s*>\s?', '', lines[i])); i += 1
            out.append('<blockquote>' + md_to_html('\n'.join(quote), up) + '</blockquote>'); continue
        if LIST_RE.match(line):
            flush(); items = []
            while i < len(lines) and (LIST_RE.match(lines[i]) or (items and lines[i].startswith('  ') and lines[i].strip())):
                lm = LIST_RE.match(lines[i])
                if lm:
                    items.append([len(lm.group(1)), not lm.group(2)[0].isdigit(), lm.group(3)])
                else:
                    items[-1][2] += '\n' + lines[i].strip()
                i += 1
            out.append(render_list(items, up)); continue
        im = re.fullmatch(IMG_MD, st)
        if im:
            flush(); src = asset(im.group(2), up)
            if src:
                cap = '<figcaption>%s</figcaption>' % esc(im.group(3)) if im.group(3) else ''
                out.append('<figure><img src="%s" alt="%s" loading="lazy">%s</figure>' % (esc(src), esc(im.group(1)), cap))
            i += 1; continue
        para.append(line); i += 1
    flush()
    return '\n'.join(out)


def render_list(items, up):
    """items: [sangría, es_viñeta, texto] → listas (anidadas si hay sangría)."""
    html, stack, indents = '', [], []
    for indent, bullet, text in items:
        tag = 'ul' if bullet else 'ol'
        while indents and indents[-1] > indent:
            indents.pop()
        if not indents or indent > indents[-1]:
            indents.append(indent)
        depth = len(indents) - 1
        while stack and stack[-1][1] > depth:
            html += '</li></%s>' % stack.pop()[0]
        if stack and stack[-1][1] == depth:
            if stack[-1][0] != tag:
                html += '</li></%s><%s><li>' % (stack.pop()[0], tag)
                stack.append((tag, depth))
            else:
                html += '</li><li>'
        else:
            html += '<%s><li>' % tag
            stack.append((tag, depth))
        html += '<br>'.join(md_inline(t, up) for t in text.split('\n'))
    while stack:
        html += '</li></%s>' % stack.pop()[0]
    return html


# --- Artículos -------------------------------------------------------------
def load_posts():
    posts = []
    for path in sorted(glob.glob(os.path.join(CONTENT, '*.json'))):
        slug = os.path.splitext(os.path.basename(path))[0]
        if not SLUG_RE.fullmatch(slug):
            warn(slug + ': nombre de archivo no válido, se omite'); continue
        try:
            data = json.load(open(path, encoding='utf-8'))
        except ValueError as e:
            warn('%s: JSON no válido (%s), se omite' % (slug, e)); continue
        base = data.get('es') if isinstance(data.get('es'), dict) else {}
        if base.get('published') is False:
            continue
        date = str(base.get('date') or '')[:10]
        if not str(base.get('title') or '').strip() or not str(base.get('body') or '').strip():
            warn(slug + ': falta título o texto en español, se omite'); continue
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
            warn('%s: fecha no válida «%s», se omite' % (slug, date)); continue
        loc = {}
        for L in LANGS:
            d = data.get(L) if isinstance(data.get(L), dict) else {}
            item = {}
            for f in ('title', 'excerpt', 'body', 'cover_alt'):
                own = str(d.get(f) or '').strip()
                item[f] = own or str(base.get(f) or '').strip()
                item[f + '_lang'] = L if own else 'es'
            if not item['excerpt']:
                plain = ' '.join(re.sub(r'[#>*_`\[\]()!~-]', '', item['body']).split())
                item['excerpt'] = (plain[:177].rsplit(' ', 1)[0] + '…') if len(plain) > 180 else plain
            loc[L] = item
        posts.append({'slug': slug, 'date': date, 'cover': str(base.get('cover') or ''), 'loc': loc})
    posts.sort(key=lambda p: (p['date'], p['slug']), reverse=True)
    return posts


def date_es(iso):
    y, m, d = (int(x) for x in iso.split('-'))
    return '%d de %s de %d' % (d, MONTHS_ES[m - 1], y)


def post_local(posts, with_meta=False):
    """Textos EN / ZH de los artículos para i18n.js (window.MARFIL_LOCAL)."""
    out = {'en': {}, 'zh': {}}
    for p in posts:
        for L in ('en', 'zh'):
            t, key = p['loc'][L], 'post.' + p['slug']
            out[L][key + '.t'] = t['title']
            out[L][key + '.x'] = t['excerpt']
            if with_meta:
                out[L][key + '.a'] = t['cover_alt']
                out[L][key + '.m'] = t['title'] + ' | Marfil Tannery'
    return out


def time_tag(iso, cls):
    return '<time class="%s" datetime="%s" data-date>%s</time>' % (cls, iso, date_es(iso))


def post_card(p, up, heading='h3'):
    t, key = p['loc']['es'], 'post.' + p['slug']
    src = asset(p['cover'], up)
    img = ('<img src="%s" alt="" loading="lazy">' % esc(src) if src
           else '<svg class="post-card__ph" aria-hidden="true"><use href="#toro"/></svg>')
    return ('<li class="post-card reveal"><a class="post-card__link" href="%sblog/%s.html">' % (up, p['slug'])
            + '<span class="post-card__img">%s</span><span class="post-card__body">' % img
            + time_tag(p['date'], 'post-card__date')
            + '<%s class="post-card__title" data-i18n="%s.t">%s</%s>' % (heading, key, esc(t['title']), heading)
            + '<span class="post-card__excerpt" data-i18n="%s.x">%s</span>' % (key, esc(t['excerpt']))
            + '<span class="post-card__more"><span data-i18n="blog.read">%s</span> <span class="arrow" aria-hidden="true">→</span></span>' % es('blog.read')
            + '</span></a></li>')


def posts_cls(n, extra=''):
    """La rejilla se adapta al número de artículos: 1 destacado, 2 a dos columnas, 3+ a tres."""
    return ('posts ' + extra + (' posts--1' if n == 1 else ' posts--2' if n == 2 else '')).replace('  ', ' ').strip()


def home_blog(posts):
    if not posts:
        return ''
    latest = posts[:HOME_POSTS]
    cards = ''.join(post_card(p, '') for p in latest)
    return f'''<section class="section section--plaster" id="blog">
  <div class="wrap">
    <div class="blog-head">
      <div class="section__head reveal">
        <h2 data-i18n="blog.title">{es('blog.title')}</h2>
        <p data-i18n="blog.lead">{es('blog.lead')}</p>
      </div>
      <a class="link reveal" href="blog/index.html"><span data-i18n="blog.all">{es('blog.all')}</span> <span class="arrow" aria-hidden="true">→</span></a>
    </div>
    <ul class="{posts_cls(len(latest))}">{cards}</ul>
  </div>
  <script>window.MARFIL_LOCAL = {js_json(post_local(latest))};</script>
</section>
'''


def blog_index(posts):
    if posts:
        listing = '<ul class="%s">%s</ul>' % (posts_cls(len(posts), 'posts--all'), ''.join(post_card(p, '../', 'h2') for p in posts))
    else:
        listing = '<p class="blog-empty" data-i18n="blog.empty">%s</p>' % es('blog.empty')
    main = f'''
<section class="page-hero">
  <div class="wrap">
    {crumbs([('../index.html', 'crumb.home'), (None, 'crumb.blog')])}
    <h1 class="page-hero__title" data-i18n="blog.h1">{es('blog.h1')}</h1>
    <p class="page-hero__lead" data-i18n="blog.lead">{es('blog.lead')}</p>
  </div>
</section>

<section class="section blog-list">
  <div class="wrap">
    {listing}
  </div>
</section>
'''
    return page('meta.blog', main, '', desc_key='meta.blogdesc', desc=es('meta.blogdesc'),
                local=post_local(posts), nav_current='blog/index.html')


def post_page(p, posts):
    slug, t = p['slug'], p['loc']['es']
    key = 'post.' + slug
    src = asset(p['cover'], '../')
    cover = ('<figure class="post__cover reveal"><img src="%s" data-i18n-attr="alt:%s.a" alt="%s" fetchpriority="high"></figure>'
             % (esc(src), key, esc(t['cover_alt']))) if src else ''
    bodies = ''
    for L in LANGS:
        lt = p['loc'][L]
        hidden = '' if L == 'es' else ' hidden'
        bodies += '      <div class="prose" data-only="%s" lang="%s"%s>\n%s\n      </div>\n' % (
            L, HTML_LANG[lt['body_lang']], hidden, md_to_html(lt['body'], '../'))
    others = [o for o in posts if o['slug'] != slug][:3]
    related = ''
    if others:
        related = f'''
<section class="section section--plaster related">
  <div class="wrap">
    <h2 class="h-sub" data-i18n="blog.more">{es('blog.more')}</h2>
    <ul class="{posts_cls(len(others), 'posts--related')}">{''.join(post_card(o, '../') for o in others)}</ul>
  </div>
</section>
'''
    crumb = ('<nav class="crumbs" data-i18n-attr="aria-label:crumb.label" aria-label="%s">' % es('crumb.label')
             + '<a href="../index.html" data-i18n="crumb.home">%s</a><span class="crumbs__sep" aria-hidden="true">/</span>' % es('crumb.home')
             + '<a href="index.html" data-i18n="crumb.blog">%s</a></nav>' % es('crumb.blog'))
    main = f'''
<article class="post">
  <header class="page-hero post-hero">
    <div class="wrap post-wrap">
      {crumb}
      {time_tag(p['date'], 'post-hero__date')}
      <h1 data-i18n="{key}.t">{esc(t['title'])}</h1>
      <p class="page-hero__lead" data-i18n="{key}.x">{esc(t['excerpt'])}</p>
    </div>
  </header>
  <div class="section post-section">
    <div class="wrap post-wrap">
      {cover}
{bodies}      <div class="post__foot">
        <a class="link link--back" href="index.html"><span class="arrow" aria-hidden="true">←</span> <span data-i18n="blog.back">{es('blog.back')}</span></a>
        <a class="btn btn--primary" href="#contacto" data-i18n="cta.quote">{es('cta.quote')}</a>
      </div>
    </div>
  </div>
</article>
{related}'''
    return page(key + '.m', main, '', title=t['title'] + ' | Marfil Tannery',
                desc_key=key + '.x', desc=t['excerpt'],
                local=post_local([p] + others, with_meta=True), nav_current='blog/index.html')


def write(path, html):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(html)
    print('escrito', path, len(html))


for p in PRODUCTS:
    write(f'productos/{p["slug"]}.html', product_page(p))
for s in SERVICES:
    write(f'servicios/{s["slug"]}.html', service_page(s))

POSTS = load_posts()
write('blog/index.html', blog_index(POSTS))
for p in POSTS:
    write(f'blog/{p["slug"]}.html', post_page(p, POSTS))
keep = {p['slug'] + '.html' for p in POSTS} | {'index.html'}
for old in glob.glob(os.path.join(ROOT, 'blog', '*.html')):
    if os.path.basename(old) not in keep:
        os.remove(old)
        print('eliminado', os.path.relpath(old, ROOT), '(artículo borrado o despublicado)')

home = re.sub(r'(<!-- blog:start[^>]*-->\n).*?(<!-- blog:end -->)',
              lambda m: m.group(1) + home_blog(POSTS) + m.group(2), HOME, count=1, flags=re.S)
if home != HOME:
    write('index.html', home)
print(f'blog: {len(POSTS)} artículo(s) publicado(s)')

en = {key: v[1] for key, v in T.items()}
zh = {key: v[2] for key, v in T.items()}
js = ('/* Generado por tools/build_pages.py — textos de páginas interiores y de la portada nueva (EN / ZH). No editar a mano. */\n'
      'window.MARFIL_PAGES = {\n  en: ' + json.dumps(en, ensure_ascii=False, indent=2).replace('\n', '\n  ')
      + ',\n  zh: ' + json.dumps(zh, ensure_ascii=False, indent=2).replace('\n', '\n  ') + '\n};\n')
write('i18n-pages.js', js)
