"""Licence PDF certificate generation.

Generates a printable A4 licence certificate with an embedded QR code.
Uses a hand-rolled minimal PDF writer (no reportlab/weasyprint needed) plus
Pillow to rasterise the QR code (Pillow is already required by qrcode).
"""
import io
import zlib

import qrcode


class _PDF:
    """Minimal single/multi-page PDF writer supporting text lines and images."""

    def __init__(self):
        self.pages = []          # list of content streams (str)
        self.images = []         # list of (width, height, rgb_bytes)
        self.current = []

    # -- content helpers ---------------------------------------------------

    def add_page(self):
        if self.current:
            self.pages.append('\n'.join(self.current))
        self.current = []

    def text(self, x, y, size, text, font='F1'):
        # PDF user space: origin bottom-left. Escape parens/backslashes.
        safe = text.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')
        self.current.append(f'BT /{font} {size} Tf {x:.2f} {y:.2f} Td ({safe}) Tj ET')

    def image(self, x, y, w, h, rgb, img_w, img_h):
        """Place a raw RGB image. y is the BOTTOM of the image."""
        idx = len(self.images)
        self.images.append((img_w, img_h, rgb))
        self.current.append('q')
        self.current.append(f'{w:.2f} 0 0 {h:.2f} {x:.2f} {y:.2f} cm')
        self.current.append(f'/Im{idx} Do')
        self.current.append('Q')

    # -- serialization -----------------------------------------------------

    def bytes(self) -> bytes:
        if self.current:
            self.pages.append('\n'.join(self.current))
            self.current = []

        objects: list[bytes] = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)  # 1-based object number

        add(b'<< /Type /Catalog /Pages 2 0 R >>')          # obj 1

        page_ids = []
        kids_placeholder = 2
        image_ids = []
        for w, h, rgb in self.images:
            data = zlib.compress(rgb)
            image_ids.append(add(
                b'<< /Type /XObject /Subtype /Image /Width ' + str(w).encode()
                + b' /Height ' + str(h).encode()
                + b' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length '
                + str(len(data)).encode() + b' >>\nstream\n' + data + b'\nendstream'
            ))

        resources = b'<< /Font << /F1 3 0 R /F2 4 0 R >> /XObject << '
        for i, img_id in enumerate(image_ids):
            resources += f'/Im{i} {img_id} 0 R '.encode()
        resources += b'>> >>'

        content_ids = []
        first_page_obj = 5 + len(self.images)
        for i, page in enumerate(self.pages):
            data = zlib.compress(page.encode('latin-1', 'replace'))
            content_ids.append(add(
                b'<< /Length ' + str(len(data)).encode() + b' /Filter /FlateDecode >>\nstream\n'
                + data + b'\nendstream'
            ))

        pages_obj_id = 2
        for i, cid in enumerate(content_ids):
            img_refs = []
            # Each page references all images; simple and valid.
            xobjects = b'<< '
            for j, img_id in enumerate(image_ids):
                xobjects += f'/Im{j} {img_id} 0 R '.encode()
            xobjects += b'>>'
            page_ids.append(add(
                b'<< /Type /Page /Parent ' + str(pages_obj_id).encode()
                + b' /MediaBox [0 0 595 842]'
                + b' /Resources << /Font << /F1 3 0 R /F2 4 0 R >> /XObject ' + xobjects + b' >>'
                + b' /Contents ' + str(cid).encode() + b' 0 R >>'
            ))

        kids = b'[' + b' '.join(f'{pid} 0 R'.encode() for pid in page_ids) + b']'
        # Insert the Pages object right after the catalog (id 2).
        objects.insert(1, b'<< /Type /Pages /Kids ' + kids + b' /Count ' + str(len(page_ids)).encode() + b' >>')
        objects[1] = b'<< /Type /Pages /Kids ' + kids + b' /Count ' + str(len(page_ids)).encode() + b' >>'
        objects[2 - 1] = b'<< /Type /Pages /Kids ' + kids + b' /Count ' + str(len(page_ids)).encode() + b' >>'
        # Font objects at ids 3 and 4 (after catalog=1, pages=2).
        objects.insert(2, b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>')
        objects.insert(3, b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')

        out = io.BytesIO()
        out.write(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        offsets = [0]
        for i, body in enumerate(objects, start=1):
            offsets.append(out.tell())
            out.write(f'{i} 0 obj\n'.encode() + body + b'\nendobj\n')
        xref_pos = out.tell()
        out.write(f'xref\n0 {len(objects) + 1}\n'.encode())
        out.write(b'0000000000 65535 f \n')
        for off in offsets[1:]:
            out.write(f'{off:010d} 00000 n \n'.encode())
        out.write(
            f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF'.encode()
        )
        return out.getvalue()


def licence_pdf(licence) -> bytes:
    """Render an A4 licence certificate for `licence` and return PDF bytes."""
    from .services import build_qr_payload

    doc = _PDF()
    doc.add_page()  # start first page content stream

    # Header band
    doc.text(60, 780, 22, 'UNITED REPUBLIC OF TANZANIA', 'F1')
    doc.text(60, 752, 16, 'e-Leseni - Business Licence Certificate', 'F2')
    doc.text(60, 726, 11, f"Issued by: {licence.lga.name}", 'F2')

    # Licence details
    rows = [
        ('Licence number', licence.licence_number),
        ('Business name', licence.business_name),
        ('Licence type', licence.licence_type.name),
        ('Holder', licence.holder.get_full_name() or licence.holder.username),
        ('Status', licence.get_status_display()),
        ('Valid from', licence.valid_from.strftime('%d %B %Y')),
        ('Valid until', licence.valid_until.strftime('%d %B %Y')),
    ]
    y = 680
    for label, value in rows:
        doc.text(60, y, 10, f'{label}:', 'F2')
        doc.text(190, y, 10, str(value), 'F1')
        y -= 24

    # QR code (verify URL)
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(build_qr_payload(licence))
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
    img_w, img_h = img.size
    rgb = img.tobytes()
    doc.image(60, y - 200, 160, 160, rgb, img_w, img_h)
    doc.text(60, y - 215, 9, 'Scan to verify this licence', 'F2')

    # Footer
    doc.text(60, 60, 9, 'This certificate is legally valid only when the QR code verification returns ACTIVE.', 'F2')

    return doc.bytes()
