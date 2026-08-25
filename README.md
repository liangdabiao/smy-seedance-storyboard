# smy-seedance-storyboard · 上美影风格短剧生成器

> 一句话：**你给一个故事，它还你一套能直接拿去出图、出视频的上美影短剧制作文档。**

"上美影"= 上海美术电影制片厂，就是《大闹天宫》《天书奇谭》《九色鹿》那种复古手绘动画的味道——概括的造型、手工感的线条、大片平涂的矿物颜料色。

测试效果：https://www.bilibili.com/video/BV1MhhG68EBH/?vd_source=86926e418c83af75f6850b5546388a79
---

## 我能用它做什么？

比如你说：

> "帮我做一个武松打虎的上美影短剧，5 集"

然后它会依次给你五样东西，全部中文、复制就能用：

| 拿到什么 | 干什么用 |
|----------|----------|
| ① 剧本 | 5 集×15 秒的分镜剧本，带说书人旁白、台词、字幕卡点 |
| ② 色盘 | 这部剧专用的颜色清单（如：朱砂红/鎏金/墨黑/青瓷绿），从头用到尾防跑色 |
| ③ 素材清单 | 角色/场景/道具的出图提示词，贴到即梦/Seedream 就能出图 |
| ④ 每集分镜 | Seedance 2.0 专用提示词（时间轴格式），整段粘贴即可出片 |
| ⑤ 尾帧说明 | 每集最后一帧的画面描述，下一集接着用，集与集无缝衔接 |

## 使用流程（三步）

**第一步：说人话提需求。** 故事可以是一句话（"做一个夸父逐日"）、一篇小说、一个神话典故，都行。

**第二步：回答几个小问题。** 它会问你集数、画幅（竖屏/横屏）、基调。不想答就说"都用默认"。

**第三步：照着文档去平台干活。**
1. 拿素材清单的提示词去**出图**（即梦/Seedream/豆包，中文直接用；Midjourney 用清单里的英文对照版）
2. 拿每集分镜去 **Seedance 2.0 出片**（第一集直接生成，第二集起把上一集视频传上去选"延长"）
3. 剪辑软件拼集、配旁白和锣鼓点，完片

## 画风怎么保证不跑偏？（通俗版）

三个实测有效的机关，**都别改**：

1. **一段固定的"风格咒语"**贴在每条提示词开头：`上美影风格（上海美术电影制片厂复古手绘动画）……`
2. **结尾两句狠命令**：`必须纯2D平涂！绝对不要阴影、不要渐变、不要3D体积感！必须大面积留白！` —— 没有它，AI 很容易把画面渲染成油画感的"假上美影"（实测踩过坑）
3. **一部剧一个色盘**，所有提示词逐字引用同一串颜色名，跨集不跑色

这些已在**生图端和视频端双双实测通过**。

## 想换个画风？

默认是"手绘平涂"主线。点名即可切换（一部剧只用一种）：

| 子风格 | 什么味道 | 参照 |
|--------|----------|------|
| 石蓝淡墨绘本 | 石蓝+淡墨，疏离怪谈绘本感，怪色点缀 | 新中式绘本 |
| 水墨淡彩 | 淡雅写意，大量留白 | 小蝌蚪找妈妈 |
| 剪纸风 | 分层剪影，对称纹样 | 葫芦兄弟 |
| 敦煌重彩 | 壁画矿物色，飘带飞天 | 九色鹿 |

## 示例项目（照着抄作业）

| 项目 | 类型 | 看点 |
|------|------|------|
| `鲁智深醉闹五台山项目/` | 醉闹喜剧 | 打斗慢速夸张、动静对比、说书人旁白 |

项目里包含：剧本、素材清单、E01-E05 分镜、使用指南，四件套齐全。

## 常见问题

**Q：出图变成 3D/有阴影渐变怎么办？**
检查提示词结尾的两句狠命令是不是被删了；还不行就追加负面词：`不要阴影，不要渐变，不要3D渲染，不要体积光，不要写实照片`。

**Q：每集多长？多少集合适？**
每集 15 秒。故事紧凑用 5 集（75 秒），完整叙事 10-20 集。

**Q：为什么提示词都是中文？**
默认面向即梦/Seedream/豆包等中文平台。用 Midjourney 时换素材清单里保留的英文对照版风格块即可。

**Q：可以不用上美影风格吗？**
这个 skill 就是为上美影而生的，风格是立身之本。其他风格请用通用视频制作流程。

## 文件说明

```
smy-seedance-storyboard/
├── SKILL.md                      # 主流程（给 AI 看的工作说明书）
├── README.md                     # 本文件（给人看的入门指南）
└── references/                   # 细则手册（按需查阅）
    ├── 上美影风格指南.md          # ★ 核心：风格块/色盘/造型规范/模板/翻车修复
    ├── seedance-manual.md        # Seedance 2.0 平台手册（含模板十七）
    ├── 好剧本.md                  # 剧本质量标准与示例
    ├── 故事转视频脚本-转换工具.md  # 故事改编模板
    ├── 优化分镜.md                # 提示词优化公式
    ├── 分镜优化与声音设计.md       # 修图/配音/音效工具指南
    └── 上美影原始提示词.txt        # 最初一批实测提示词（溯源用）
```



项目首发于linux.do社区，感谢佬友认同： https://linux.do



## Repository Overview

This is a Chinese-language repository for **上美影风格（Shanghai Animation Film Studio vintage hand-drawn animation style）AI short-drama production**, combining Claude Code (script and storyboard generation), Midjourney / GPT-Image-2 / Seedream / Nano Banana Pro (asset generation), and Seedance 2.0 (video generation). The workflow transforms stories, myths, and novels into multi-episode AI video series with consistent 上美影 visual style (ink wash + gouache texture, traditional mineral pigment colors, bold simplified contours, film grain) and character design.

## Core Workflow

The production process follows these steps:

1. **Script Development** - Converting source material into four-act structure scripts (说书人旁白体制 recommended)
2. **色盘声明 (Palette Declaration)** - Declaring the crew palette string (主四色 + 0-2 扩展色), quoted verbatim by all asset and storyboard prompts
3. **Asset Generation Plan** - Creating numbered prompts for characters (C01-C99), scenes (S01-S99), beasts (C-numbered, beast scene template), and props (P01-P99), all carrying the 上美影 style block
4. **Image Generation** - Using Midjourney / GPT-Image-2 / Seedream / Nano Banana Pro to generate visual assets with the unified 上美影 style block prefix
5. **Storyboard Script Generation** - Creating Seedance 2.0 prompts in time-axis format (0-3s, 3-6s, 6-9s, 9-12s, 12-15s), first line = fixed 上美影 style line + palette
6. **Video Generation** - Using Seedance 2.0 platform with video extension feature for episode chaining
 
## Key File Patterns

- `[Title]_剧本.md` - Four-act script with episode breakdown (起承转合 structure)
- `[Title]_素材清单.md` - Numbered asset generation prompts with English style prefixes
- `[Title]_E[XX]_分镜.md` - Individual episode storyboard scripts for Seedance 2.0

## Asset Numbering Convention

| Prefix | Range | Type | Example |
|--------|-------|------|---------|
| C | C01-C99 | Characters (multiple angles per character) | C01 林冲·正面全身 |
| S | S01-S99 | Scenes/Locations | S01 沧州草料场·雪景 |
| P | P01-P99 | Props/Objects | P01 长枪 |

## Seedance 2.0 Prompt Structure

Each episode script contains:

1. **素材上传清单** - Table mapping asset IDs to upload slots
2. **Seedance Prompt** - Time-axis format description:
   - Style and atmosphere specification
   - 0-3s: Scene establishment
   - 3-6s: Subject introduction
   - 6-9s: Development/conflict
   - 9-12s: Climax/transition
   - 12-15s: Conclusion
   - Sound design (music + SFX + dialogue)
   - Asset references (@图片X syntax)
3. **尾帧描述** - Final frame description for next episode continuity

## Video Extension (Episode Chaining)

For episodes 2+, use video extension to maintain continuity:
- Upload previous episode video as @视频1
- Start prompt with: `将@视频1延长15s`
- This creates seamless transitions between episodes

## Style Consistency

**单一事实来源**：`.claude/skills/smy-seedance-storyboard/references/上美影风格指南.md` defines the complete 上美影 style system (style blocks, hard constraint layer, negative prompts, palette, character design rules, asset templates). **All asset prompts are written in Chinese by default** (即梦/Seedream native); they begin with the unified CN style block and END with the CN hard constraint (实测：防止渐变/阴影/3D体积漂移). Default block:
```
上美影风格（上海美术电影制片厂复古手绘动画），中国传统手绘二维动画，传统矿物颜料纯平涂色块，大胆概括的轮廓线，带手工感的不完美笔触轮廓，装饰性平面背景纹样，模拟动画胶片颗粒感，浓郁的中国幻想美学，主色：[本剧色盘中文]。必须纯2D平涂！绝对不要阴影、不要渐变、不要3D体积感！必须大面积留白！
```
English counterpart (optional, Midjourney / GPT-Image only):
```
vintage Shanghai Animation Film Studio aesthetic, traditional Chinese hand-drawn 2D animation, flat color fields in traditional mineral pigment colors, bold and simplified contours, imperfect hand-drawn brushstroke outlines, decorative flat background patterns, simulated animated film grain, rich Chinese fantasy aesthetics, [本剧色盘英文], ultra-detailed, 8K. CRITICAL: 2D FLAT COLORS ONLY. ABSOLUTELY NO SHADING, NO GRADIENTS, NO 3D VOLUME. Vast empty negative space is MANDATORY.
```
Seedance video prompt first line (精简版):
```
上海美术电影制片厂经典手绘动画风格，手绘墨线轮廓，水粉平涂上色、保留颜料笔触与手工感，矿物颜料色（[本剧主色简写]），概括造型，胶片颗粒感，不要3D渲染、不要写实感、不要体积光
```

Character differentiation uses distinct color schemes (专属主色) and traditional decorative patterns (专属纹样), plus 怪色点缀 accents (muted red / dusty pink / gold brown, small areas only). Character proportions follow 上美影 rules (adults 5-7 heads tall, children 3-4, beasts exaggerated), NOT the realistic 二八比例. Lighting is expressed as 色块对比 (juxtaposed flat color fields), never as volumetric/soft lighting words.

**禁用词**：photorealistic、皮肤纹理、二八比例、anime、cel-shading、赛璐珞，以及 soft glow / bloom / volumetric lighting / airbrush / 渐变 / 晕染 / 色晕 / 柔光（破坏纯平涂）。

**动画风格红利**：上美影手绘动画风格天然规避写实真人脸部素材的审核限制。

## Important Constraints

- **Max 9 images** per Seedance 2.0 generation
- **Max 3 videos** (total 15s) as reference
- **Sensitive words** may cause generation failures (e.g., "江湖人士")
- **Video editing** capability is limited - regeneration required for most changes
- **Instruction following** can be inconsistent with complex prompts (300+ words)

## Camera Movement Keywords (Chinese)

- 推镜头/拉镜头 (Push/Pull)
- 摇镜头 (Pan)
- 移镜头 (Truck)
- 跟镜头 (Follow)
- 环绕镜头/360度旋转 (Orbit/360°)
- 升降镜头 (Crane)
- 希区柯克变焦 (Hitchcock zoom)
- 一镜到底 (One shot)
- 手持晃动 (Handheld shake)

## Skill Usage

Invoke the custom skill for 上美影风格 video script generation:
```
/skill smy-seedance-storyboard
```

The skill handles: story analysis, four-act script structure (说书人旁白体制), palette declaration, asset planning with 上美影 templates, and Seedance 2.0 formatted prompts with fixed style line.

## Reference Documentation

- `.claude/skills/smy-seedance-storyboard/SKILL.md` - Skill definition and workflow (上美影风格版)
- `.claude/skills/smy-seedance-storyboard/references/上美影风格指南.md` - **上美影风格单一事实来源**（风格块/色盘/造型规范/资产模板/子风格模块）
- `.claude/skills/smy-seedance-storyboard/references/上美影原始提示词.txt` - 原始实测提示词素材（山海经5条+水浒3条成品示例）
- `.claude/skills/smy-seedance-storyboard/references/seedance-manual.md` - Complete Seedance 2.0 manual (含模板十七：上美影国风动画类)
- `.claude/skills/smy-seedance-storyboard/references/故事转视频脚本-转换工具.md` - Story adaptation template
