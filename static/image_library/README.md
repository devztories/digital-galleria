# Image library — ONE folder for every picture

All category / product / colour pictures live **here**, flat (no sub-folders).
Nothing is uploaded through the admin any more, so no external storage
(Supabase etc.) is used for catalogue images.

## Adding pictures
1. Copy the image files into this folder (any name; `.webp .jpg .png .avif .gif`).
   Suggested: 900x900 px square, .webp, under 200 KB.
2. Commit + deploy.
3. In the admin (Products / Categories / Colour variants) press
   **Choose from image library**, tick the pictures, save.
   The first picture ticked for a colour becomes its main image.

Admin -> **Image Library** shows every file here and where it is used.

## Demo catalogue (optional auto-matching)
Files named like this are picked up automatically for the demo products of
`products/catalog_data.py` (loaded by `python manage.py sync_catalog`) when no
image was chosen in the admin:

    <category>__cover.webp                      category cover
    <category>__<product>__<colour>__1.webp     colour pictures (1 = main), 2, 3 ...
    <category>__<product>__1.webp               product without colours

An image picked in the admin always wins over this auto-matching.
