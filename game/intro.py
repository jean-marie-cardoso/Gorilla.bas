# intro.py — court écran de marque, sans clic obligatoire
import asyncio

import pygame

from config import FPS, VIRTUAL_W
from menu import draw_menu_background


async def show_intro(game, duration=0.7):
    """Affiche un splash court puis continue seul.

    Retourne ``True`` pour continuer et ``False`` après Échap/fermeture. Une
    touche ou un clic passe seulement le splash: le menu reste l'unique écran
    où une action est nécessaire pour démarrer.
    """
    elapsed = 0.0
    while elapsed < max(0.0, float(duration)):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.quit_requested = True
                return False
            if game.is_resize_event(event):
                game.resize_display(event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.quit_requested = True
                    return False
                if event.key in (pygame.K_F11, pygame.K_f):
                    game.toggle_fullscreen()
                else:
                    return True
            elif event.type in (
                pygame.MOUSEBUTTONDOWN,
                pygame.FINGERDOWN,
            ):
                return True

        draw_menu_background(game)
        panel = pygame.Surface((430, 174), pygame.SRCALPHA)
        pygame.draw.rect(panel, (3, 13, 31, 218), panel.get_rect(), border_radius=20)
        pygame.draw.rect(
            panel,
            (255, 210, 72, 160),
            panel.get_rect(),
            width=2,
            border_radius=20,
        )
        game.vsurf.blit(panel, panel.get_rect(center=(VIRTUAL_W // 2, 194)))

        title = game.font_big.render("GORILLAS", True, (255, 215, 76))
        game.vsurf.blit(title, title.get_rect(center=(VIRTUAL_W // 2, 151)))
        tagline = game.font.render("BANANES  •  VENT  •  DÉGÂTS", True, (255, 255, 255))
        game.vsurf.blit(tagline, tagline.get_rect(center=(VIRTUAL_W // 2, 194)))
        subtitle = game.font_small.render(
            "Le duel culte, remis au goût du jour",
            True,
            (188, 216, 238),
        )
        game.vsurf.blit(subtitle, subtitle.get_rect(center=(VIRTUAL_W // 2, 229)))

        game.blit_scaled()
        pygame.display.flip()
        elapsed += game.clock.tick(FPS) / 1000.0
        await asyncio.sleep(0)

    return True
