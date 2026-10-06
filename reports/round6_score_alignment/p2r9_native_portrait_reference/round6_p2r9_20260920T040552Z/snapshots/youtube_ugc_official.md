Title: YouTube datasets for video compression and quality assessment research

URL Source: https://media.withyoutube.com/ugc-dataset

Published Time: Wed, 09 Sep 2026 23:45:04 GMT

Markdown Content:
![Image 1](https://storage.googleapis.com/ugc-dataset/website/ugc_dataset_logo.svg)Explore Download About

![Image 2](https://storage.googleapis.com/ugc-dataset/website/ugc_dataset_logo.svg)

More Datasets

[UGC](https://media.withyoutube.com/[[rootPath]])[SFV+HDR](https://media.withyoutube.com/[[rootPath]]sfv-hdr)[UGC Transcodes](https://media.withyoutube.com/[[rootPath]]publications/ugc_transcodes)[Publications](https://media.withyoutube.com/[[rootPath]]publications)

![Image 3](https://storage.googleapis.com/ugc-dataset/website/ugc_dataset_logo.svg)Explore Download About

UGC Dataset

 A large scale dataset containing YouTube User Generated Content intended for video compression and quality assessment research. 

UGC Dataset

 A large scale dataset containing YouTube User Generated Content intended for video compression and quality assessment research. 

# YouTube-UGC Dataset

This YouTube dataset is a sampling from thousands of User Generated Content (UGC) as uploaded to YouTube distributed under the Creative Commons license. This dataset was created in order to assist in the advancement of video compression and quality assessment research of UGC videos.

![Image 4](https://storage.googleapis.com/ugc-dataset/website/website_thumbnails_cropped.jpg)

# What is a UGC video clip

UGC videos are uploaded by users and creators. These videos are not always professionally curated and often suffer from perceptual artifacts. For the purpose of this dataset, we've selected original videos with specific and sometimes substantial perceptual quality issues, like blockiness, blur, banding, noise, jerkiness, and so on.

[Video 1](https://storage.googleapis.com/ugc-dataset/website/previews_Vlog_480P-5275_cropped_540x304.mp4)

# Challenges in UGC

A common assumption of much video quality and compression research is that the original video is pristine (as in the top frame), and any operation on the original (processing, compression, etc) makes it worse. Most research measures how good the resulting video is by comparing it to the original. However, such an assumption breaks down in practice as most upoads are not usually pristine (as in the bottom frame).

![Image 5](https://storage.googleapis.com/ugc-dataset/website/original_vs_uploaded.png)

# Dataset Specs

*   Around 1500 video clips with a duration of 20 seconds each.   
  
*   Categories 
    *   Animation, Cover Song, Gaming, HDR, How-To, Lecture, Live Music, Lyric Video, Music Video, News Clip, Sports, Television Clip, Vertical Video, Vlog, and VR

  
*   Resolutions 
    *   360P, 480P, 720P, and 1080P for all categories (except for HDR and VR) 
    *   4K for HDR, Gaming, Sports, Vertical Video, Vlog, and VR genres.

![Image 6](https://storage.googleapis.com/ugc-dataset/website/website_categories_cropped.png)

# Subjective Quality Scores

*   Mean Opinion Scores (MOS) available for all video clips.   
  
*   MOS for entire video clips 
    *   All video clips were rated by 100+ subjects using crowdsourcing. 
    *    The MOS range is [1, 5], where 1 means bad quality and 5 means excellent quality. 

  
*   MOS for chunks 
    *   Additional MOS for three overlapping 10 second chunks (the first frame starts at 0, 5, and 10 seconds) are also provided to investigate influence of scene changes.

  
*   DMOS for selected content categories (Gaming, Sports, and Vlog) 
    *   Three VP9 variants: Video-On-Demand (VOD), Video-On-Demand with Lower Bitrate (VODLB), and Constant Bitrate (CBR), using the recommended VP9 settings and target bitrates.

![Image 7: MOS image](https://storage.googleapis.com/ugc-dataset/website/website_UGC_MOS_sample.png)

# UGC Content Labels

*   600+ labels for studying the relationship between UGC content and perceptual quality. 
      

    *    Each video was assigned 12 candidate YT8M labels, and then refined through a crowd-sourcing subjective test. Every label on each video was voted by more than 10 subjects. The corresponding label confidence is defined as the actual votes divided by the total shows. 

  

![Image 8: Content labels](https://storage.googleapis.com/ugc-dataset/website/website_content_labels.png)

Download

 This YouTube dataset will be updated monthly. Users are responsible for refreshing their copy, and deleting clips that have been removed from the latest version. 

# Videos

This dataset currently contains about 1500 (pre-YouTube transcoded) video clips. The length of each video is around 20 seconds. Two versions of original videos are available: RAW YUV and H264 CRF 10.   
  
 We also provides VP9 variants for Gaming, Sports, and Vlog videos.   
  
 We suggest using [gsutil](https://cloud.google.com/storage/docs/gsutil/commands/cp) to download clips.   
  
[](https://console.cloud.google.com/storage/browser/ugc-dataset/original_videos)

[DOWNLOAD ORIGINAL (RAW, 2TB)](https://console.cloud.google.com/storage/browser/ugc-dataset/original_videos)[](https://console.cloud.google.com/storage/browser/ugc-dataset/original_videos)[ORIGINAL (H264, 110GB)](https://console.cloud.google.com/storage/browser/ugc-dataset/original_videos_h264)[VP9 VARIANTS (20GB)](https://console.cloud.google.com/storage/browser/ugc-dataset/vp9_compressed_videos)

# Subjective data

Mean Opinion Scores (MOS) are provided for entire videos and corresponding 10 second chunks (the first frame starts at 0, 5, and 10 seconds).   
  
 Differential MOS (DMOS) are available for Gaming, Sports, and Vlog categories.   
  
 Content labels are provided for all originals.   
  
[](https://storage.cloud.google.com/ugc-dataset/original_videos/MOS_for_YouTube_UGC_dataset.xlsx)

[DOWNLOAD MOS](https://storage.cloud.google.com/ugc-dataset/original_videos/MOS_for_YouTube_UGC_dataset.xlsx)[](https://storage.cloud.google.com/ugc-dataset/original_videos/MOS_for_YouTube_UGC_dataset.xlsx)[DMOS](https://storage.cloud.google.com/ugc-dataset/original_videos/DMOS_for_YouTube_UGC_dataset.xlsx)[CONTENT LABELS](https://storage.cloud.google.com/ugc-dataset/original_videos/Content_label_for_YouTube_UGC_dataset.xlsx)

# Attribution

The videos are shared under Creative Commons [CC BY](https://creativecommons.org/licenses/by/4.0/legalcode) license. We thank our creators who uploaded the videos under this license. The list of attributions for all the shared videos in this dataset can be downloaded from the link below.   
  
[](https://storage.googleapis.com/ugc-dataset/ATTRIBUTION)

[DOWNLOAD ATTRIBUTION](https://storage.googleapis.com/ugc-dataset/ATTRIBUTION)[](https://storage.googleapis.com/ugc-dataset/ATTRIBUTION)

# Cite us

The YouTube UGC dataset is freely available to the research community. If you use our database in your research, please cite it as follows:   
  
 Yilin Wang, Sasi Inguva, Balu Adsumilli, ["YouTube UGC dataset for video compression research"](https://ieeexplore.ieee.org/abstract/document/8901772), IEEE 21st International Workshop on Multimedia Signal Processing (MMSP) 2019.

About

# Who are we?

We are the YouTube Media Algorithms team, working on video/audio transcoding, video/audio quality assessment, and media processing infrastructure.   
  
 We created this dataset in order to encourage and facilitate research that considers the practical and realistic requirements of video processing infrastructure in regards to video compression and quality assessment.

  
  

You can reach us at youtube-ugc-dataset@googlegroups.com

Explore

Content

Resolution

[![Image 9](https://storage.googleapis.com/ugc-dataset/website/youtube_footer_logo.svg)](https://www.youtube.com/)

[Policy & Safety](https://www.youtube.com/yt/about/policies/)[Copy Right](https://www.youtube.com/yt/about/copyright/)

[Brand Guidelines](https://www.youtube.com/yt/about/brand-resources/)[Privacy](https://www.google.com/policies/privacy/)[Terms](https://www.youtube.com/t/terms)
