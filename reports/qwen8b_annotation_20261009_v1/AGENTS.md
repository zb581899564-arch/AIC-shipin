# Dataset annotation workspace

User authorized dataset annotation as preparation for Qwen8B fine-tuning.
Only annotate the TVSum media and PNGs explicitly assigned by the current task.
Read visual inputs with native video/image tools. Do not train models, start GPUs,
send files to remote hosts, access competition test media, inspect old experiments,
install tools, search the web, or use other models/subagents.
Write raw annotation outputs only to the exact assigned output directory.
Never overwrite a successful raw output. Failed or partial results remain visible.
Record actual tool observation coverage; unseen frames are UNKNOWN, not negative.
Crop coordinates refer to each original frame, not its display thumbnail.
This is a new dataset version, not a modification of previous frozen experiments.
