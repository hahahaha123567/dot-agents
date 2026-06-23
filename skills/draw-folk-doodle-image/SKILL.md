---
name: draw-folk-doodle-image
description: 将用户提供或描述的图像转化为单一的装饰性民间平面插图，并融入涂鸦元素。适用于用户要求“民间插画”“folk illustration”“涂鸦风”“童趣”“异想天开”“白纸上的平面装饰画”“把这张图变成可爱手工插画”等图片生成或图片编辑任务。
---

# Folk Doodle Image

## Core Style

When this skill is used, generate or edit the image into one unified decorative folk flat illustration with doodle elements.

Use this fixed style direction as the base prompt:

```text
请将整个图像转化为单一的装饰性民间平面插图，融入涂鸦元素。使用大胆而俏皮的色彩调色板，与原图像完全不同。将所有细节简化为干净、平面的形状，带有手工制作、略显不完美的感觉，仿佛画在一张白纸上。整体风格应显得可爱、童趣十足且异想天开。
```

## Image Editing Workflow

1. Preserve the main subject, composition role, and recognizable scene logic from the user's source image.
2. Replace the rendering style completely: no realism, no photographic lighting, no 3D, no painterly depth.
3. Simplify all visible details into flat decorative shapes, playful outlines, tiny doodle marks, hand-drawn ornaments, and folk-art motifs.
4. Change the palette decisively so it feels unrelated to the original image colors.
5. Keep the background like white paper unless the user explicitly asks for another background.
6. Make the result read as one coherent illustration, not a collage or a mixed-style transformation.

## Prompt Additions

Add these constraints when composing the final image prompt:

- Clean flat shapes, decorative folk art composition
- Bold playful colors, childlike but polished
- Handmade imperfect edges, charming asymmetry
- Doodle stars, dots, scallops, small leaves, simple symbols, and naive line accents
- White paper background, no texture-heavy canvas unless requested
- Whimsical, cute, innocent, storybook-like mood

## Negative Constraints

Avoid:

- Photorealism, realistic skin, lens effects, cinematic lighting
- 3D render, glossy plastic, metallic realism
- Heavy shadows, gradients, complex perspective, realistic depth
- Preserving the original image palette too closely
- Mixed media collage unless the user specifically asks for collage
- Text in the image unless the user explicitly requests it

## Output Behavior

If the user provides an image, use image editing. If the user only describes an image, generate a new image from the description using the same style. Do not ask for confirmation unless the required source image is missing and the request depends on it.
