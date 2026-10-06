# LIVE-YT VC 使用边界询问稿（未发送）

状态：`DRAFT_ONLY_NOT_SENT`。本文件不构成授权，也未通过邮件、issue、表单或私信发送。

## 拟询问对象与公开来源

- 对象：Cheng-Han Lee 及 LIVE-YT VC 作者/维护者团队。
- 公开来源：论文作者列表 `arXiv:2604.24947v1`，以及第一方仓库 <https://github.com/steven413d/LIVE-YT-VideoCropping>（维护账户 `steven413d`）。
- 如用户后续明确授权联系，应由用户选择实际渠道；本轮不代发。

## English draft

Subject: Permission clarification for limited local research evaluation using LIVE-YT VC

Dear LIVE-YT VC authors and maintainers,

We are conducting a local, non-commercial research evaluation for a video highlight and reframing competition project. We would like to use a strictly limited subset of the original LIVE-YT VC data only as an offline diagnostic reference. At this stage we would use at least eight source videos, keep source videos as independent groups, and evaluate only the original sparse human 9:16 annotations. We would not redistribute the videos or labels, upload them to an external API, or include them in a submission package.

Could you please confirm each of the following separately?

1. May we download and locally retain the LIVE-YT VC `study_videos` and `video_bbox_labels.csv` for non-commercial research evaluation in a competition-related project?
2. Does that permission cover both the dataset's derived six-second video clips and the original sparse human bounding-box annotations, rather than only the repository code?
3. Are the selected study videos individually traceable to YouTube-UGC or LSVQ, with the attribution or notice required by the underlying source included in the release? If so, where is that per-video mapping recorded?
4. May we compute and privately retain aggregate IoU-style diagnostic results and hashes without publishing per-video labels or coordinates?
5. Is model training or fine-tuning on these videos/annotations permitted? We will treat this as **not permitted** unless you explicitly answer yes.
6. Is using a model evaluated or trained with this dataset in a competition submission permitted? We will treat this as **not permitted** unless you explicitly answer yes.
7. May a trained model or other non-reconstructive derivative be published? We will treat this as **not permitted** unless you explicitly answer yes.
8. What citation, copyright notice, attribution, deletion/update obligation, or redistribution restriction must we follow?
9. Do the same terms apply to LIVE-YT VC++? We currently intend to treat VC++ as post-processed labels, not direct human ground truth.

If helpful, we can limit the request to evaluation-only use of eight videos and the original sparse labels, with no training, redistribution, public release, or competition packaging.

Sincerely,
[Name / affiliation to be supplied by the user]
