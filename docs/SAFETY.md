# Safety

- Do not flash, erase, factory-reset, or recalibrate a physical MicroFreak
  from this project. That needs a separate explicit approval. The offline
  recipe is `scripts/release_recipe.py`. It builds the image in memory and
  prints its hash. The payload is not stored here, and flashing is not approved.
- Do not modify the bootloader, factory data, device identity, calibration,
  or the keyboard, matrix, or OLED coprocessor images.
- Do not commit `.mff`, `.bin`, `.raw`, or bootloader dumps. `.gitignore`
  refuses those names.
- The recovery gesture is Shift + Arp + OCT | MOD held at power-on. It is
  bootloader behavior. Orchid Mode is only allowed after normal startup.
- Turning Orchid Mode on or off must not write presets, calibration, or
  settings. The host keeps the flag in memory. Power-on defaults to off.
- `firmware/boundaries.py` lists the eight ranges the recipe changes.
  Ordinary mode changes do not write presets, calibration, or settings.
