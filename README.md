# FusionX template library

The Elementor section templates used by the **FusionX Templates** button in the FusionX theme
(Elementor editor → the orange **FX** button).

This is a copy of the WoodMart (XTemos) Elementor template library, kept here so the theme does not
depend on the original vendor's servers. It is mirrored with the original vendor's permission.

## Layout

| Path | Contents |
| --- | --- |
| `index.json` | Template list: id, title, slug, tags, preview image |
| `templates/<id>.json` | Elementor data for one template (`content`, `page_settings`) |
| `media/<host>/...` | Every image the templates use, and the preview images |
| `tools/mirror.py` | The script that made the copy |

Image and link URLs inside the JSON files use the placeholder `{{LIB}}`. The theme replaces it with
the address this repository is served from, which by default is
`https://raw.githubusercontent.com/Shashankphatkure/fusionx-template-library/main`.

To serve the library from somewhere else, copy this repository there and add to the site:

```php
add_filter( 'fusionx_template_library_url', function () {
	return 'https://example.com/fusionx-template-library';
} );
```

To hide the library and keep only the templates bundled in the theme:

```php
add_filter( 'fusionx_template_library_remote', '__return_false' );
```

## How the theme uses it

1. When the template window opens, the site fetches `index.json` once and caches it for 12 hours.
2. When a template is inserted, the site downloads `templates/<id>.json`, and Elementor copies the
   images it uses into the site's Media Library.

## Updating

```sh
python tools/mirror.py templates   # new templates only (existing files are kept)
python tools/mirror.py media       # images that are not here yet
python tools/mirror.py index       # rebuild index.json
```
