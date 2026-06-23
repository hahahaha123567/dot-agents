---
name: draw-crochet-doll-image
description: 将用户提供或指定的图片转换为温馨钩针玩偶、毛线公仔、手工编织角色风格。适用于用户要求“玩偶风格”“钩针角色”“毛线玩偶”“毛公仔”“amigurumi”“crochet doll”“把这张图变成手工钩织玩偶”等图片编辑或风格转换任务。
---

# Draw Crochet Doll Image

## Core Style

When this skill is used, transform the provided image subject into a warm handcrafted crochet doll character. Preserve the source image's main subject identity, pose, recognizable composition role, and key accessories when possible, but replace the rendering with soft yarn texture, visible crochet stitches, plush proportions, and nostalgic handmade doll aesthetics.

Use this base prompt:

```text
一个手工钩织的[subject]玩偶，使用柔软的纱线质感和复杂的针织细节制成。身着鲜艳的[color1]色调点缀和精致的[color2]色服装，手持一个小[prop]。设置在一个温馨的[setting]中，温暖的柔和氛围，迷人的手工美学，怀旧的毛公仔风格。
```

## Slot Filling

- `[subject]`: Use the source image's main subject. If the subject is a person, describe them generically by visible role, outfit, hairstyle, or pose rather than private identity unless the user provides a name.
- `[color1]`: Choose a bright accent color from the source image when it helps recognition; otherwise choose a cheerful complementary color.
- `[color2]`: Choose the clothing base color. Keep it compatible with `[color1]` and avoid muddy palettes.
- `[prop]`: Preserve a recognizable object from the source image if available. If none exists, choose a small fitting handmade prop, such as a tiny flower, book, cup, star, heart, bag, or tool.
- `[setting]`: Preserve the source scene category when important; otherwise use a cozy setting such as a softly lit craft room, wooden shelf, warm nursery corner, knitted blanket, or small handmade diorama.

## Image Editing Workflow

1. Identify the source image's main subject, silhouette, pose, key colors, accessories, and scene context.
2. Convert the subject into a single coherent crochet doll or amigurumi-like plush character.
3. Emphasize tactile material: soft yarn fibers, visible stitch loops, complex knitted details, stuffed rounded forms, handmade seams, and gentle fabric imperfections.
4. Keep the mood warm, soft, nostalgic, and charming rather than glossy, cinematic, or toy-commercial-like.
5. Preserve enough subject cues for recognition while simplifying fine details into crocheted shapes.
6. Avoid adding text unless the user explicitly asks for it.

## Prompt Additions

Add these constraints when composing the final image prompt:

- Warm handcrafted crochet doll character
- Soft yarn texture, visible stitch loops, intricate knitted details
- Rounded plush proportions, handmade seams, gentle imperfections
- Cozy warm setting, soft diffused lighting, nostalgic plush toy mood
- Charming handmade aesthetic, tactile fabric surface, not plastic

## Negative Constraints

Avoid:

- Photorealistic skin, realistic hair strands, hard plastic toy surfaces
- 3D glossy render, vinyl figure, porcelain doll, clay figure, action figure
- Cinematic lighting, heavy shadows, cold sci-fi atmosphere
- Sharp mechanical details that fight the soft crochet material
- Overly busy backgrounds that hide the yarn texture
- Text in the image unless explicitly requested

## Output Behavior

If the user provides an image, use image editing and transform the image into the crochet doll style. If the user describes a subject without providing an image, generate a new warm crochet doll character using the same style. Do not ask for confirmation unless the task depends on a missing source image.
