# ui.py — briques UI simples, sombres et alignees sur les pixels
import pygame

from config import CREAM, HUD_BG, HUD_BORDER, INK, STATUS_BG


def render_text(font, text, color=CREAM, antialias=True):
    """Texte antialiasé pour rester lisible après agrandissement."""
    return font.render(str(text), antialias, color)


def clip_text(font, text, max_width):
    """Coupe un nom trop long sans faire deborder sa carte."""
    text = str(text)
    if font.size(text)[0] <= max_width:
        return text
    suffix = "..."
    while text and font.size(text + suffix)[0] > max_width:
        text = text[:-1]
    return text + suffix


def draw_panel(
    surface,
    rect,
    fill=HUD_BG,
    border=HUD_BORDER,
    accent=None,
    shadow=True,
):
    """Panneau arcade carre avec ombre et liseres; retourne son Rect."""
    rect = pygame.Rect(rect)
    if shadow:
        shadow_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (7, 6, 20, 145), shadow_surf.get_rect())
        surface.blit(shadow_surf, (rect.x + 3, rect.y + 3))

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect())
    pygame.draw.rect(panel, border, panel.get_rect(), 1)
    pygame.draw.line(panel, (255, 255, 255, 28), (1, 1), (rect.w - 2, 1), 1)
    pygame.draw.line(panel, (0, 0, 0, 70), (1, rect.h - 2), (rect.w - 2, rect.h - 2), 1)
    if accent is not None:
        pygame.draw.rect(panel, accent, (0, 0, 4, rect.h))
        pygame.draw.rect(panel, accent, (4, 0, max(0, rect.w - 4), 2))
    surface.blit(panel, rect.topleft)
    return rect


def draw_center_text(
    surface,
    font,
    text,
    y,
    color=(255, 255, 255),
    shadow=None,
    antialias=True,
):
    img = render_text(font, text, color, antialias)
    x = surface.get_width() // 2 - img.get_width() // 2
    if shadow is not None:
        shadow_img = render_text(font, text, shadow, antialias)
        surface.blit(shadow_img, (x + 2, y + 2))
    surface.blit(img, (x, y))
    return img.get_rect(topleft=(x, y))


def draw_toast(surface, font, text, y=None, color=CREAM, max_width=520):
    """Message de statut lisible sur la ville, quelle que soit sa couleur."""
    if not text:
        return None
    label = clip_text(font, text, max_width - 24)
    img = render_text(font, label, color)
    width = min(max_width, img.get_width() + 24)
    height = img.get_height() + 14
    if y is None:
        y = surface.get_height() - height - 10
    rect = pygame.Rect(
        surface.get_width() // 2 - width // 2,
        int(y),
        width,
        height,
    )
    draw_panel(surface, rect, fill=STATUS_BG, border=(164, 94, 125), shadow=True)
    pygame.draw.rect(surface, (255, 197, 82), (rect.x + 7, rect.centery - 2, 4, 4))
    surface.blit(img, (rect.centerx - img.get_width() // 2 + 4, rect.centery - img.get_height() // 2))
    return rect


def draw_key_hint(surface, font, text, x, y):
    """Petit cartouche reutilisable pour les raccourcis."""
    img = render_text(font, text, (224, 211, 227))
    rect = pygame.Rect(x, y, img.get_width() + 12, img.get_height() + 8)
    draw_panel(surface, rect, fill=(INK[0], INK[1], INK[2], 205), shadow=False)
    surface.blit(img, (rect.x + 6, rect.y + 4))
    return rect
