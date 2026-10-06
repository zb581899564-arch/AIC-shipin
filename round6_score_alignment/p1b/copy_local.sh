#!/bin/bash
set -e
echo '--- P01 0ReDuH0_rpI_210.0_360.0.mp4'
timeout 300 ssh -o BatchMode=yes aic-inspur-home "cat '/home/inspur/aic_video_data/videos/0/0ReDuH0_rpI_210.0_360.0.mp4'" > 'round6_score_alignment/p1b/media/0ReDuH0_rpI_210.0_360.0.mp4' 2>/dev/null
echo '85999bd9326423e801b01b12dfba7e5806042c6c3fae721a8517726a9e545d3d' | tr -d '
' > /tmp/exp_P01.txt
H=$(sha256sum 'round6_score_alignment/p1b/media/0ReDuH0_rpI_210.0_360.0.mp4' | cut -d' ' -f1)
if [ "$H" = "$(cat /tmp/exp_P01.txt)" ]; then echo "P01 SHA_MATCH $H"; else echo "P01 SHA_MISMATCH got=$H expected=$(cat /tmp/exp_P01.txt)"; fi
echo '--- P02 FQEW3xLOa9M_210.0_360.0.mp4'
timeout 300 ssh -o BatchMode=yes aic-inspur-home "cat '/home/inspur/aic_video_data/videos/f/FQEW3xLOa9M_210.0_360.0.mp4'" > 'round6_score_alignment/p1b/media/FQEW3xLOa9M_210.0_360.0.mp4' 2>/dev/null
echo 'c32486d888ec80bd105cd08d1ba1c3623bf0d2ce9ded05941ca027389bd69323' | tr -d '
' > /tmp/exp_P02.txt
H=$(sha256sum 'round6_score_alignment/p1b/media/FQEW3xLOa9M_210.0_360.0.mp4' | cut -d' ' -f1)
if [ "$H" = "$(cat /tmp/exp_P02.txt)" ]; then echo "P02 SHA_MATCH $H"; else echo "P02 SHA_MISMATCH got=$H expected=$(cat /tmp/exp_P02.txt)"; fi
echo '--- P03 GYH6HdJ6nao_210.0_360.0.mp4'
timeout 300 ssh -o BatchMode=yes aic-inspur-home "cat '/home/inspur/aic_video_data/videos/g/GYH6HdJ6nao_210.0_360.0.mp4'" > 'round6_score_alignment/p1b/media/GYH6HdJ6nao_210.0_360.0.mp4' 2>/dev/null
echo '6c0e966e42f86f151bf49cde2e7e00538f70313501f8899818afbd68acbf9647' | tr -d '
' > /tmp/exp_P03.txt
H=$(sha256sum 'round6_score_alignment/p1b/media/GYH6HdJ6nao_210.0_360.0.mp4' | cut -d' ' -f1)
if [ "$H" = "$(cat /tmp/exp_P03.txt)" ]; then echo "P03 SHA_MATCH $H"; else echo "P03 SHA_MISMATCH got=$H expected=$(cat /tmp/exp_P03.txt)"; fi
echo '--- P04 QPcwfuStFnU_210.0_360.0.mp4'
timeout 300 ssh -o BatchMode=yes aic-inspur-home "cat '/home/inspur/aic_video_data/videos/q/QPcwfuStFnU_210.0_360.0.mp4'" > 'round6_score_alignment/p1b/media/QPcwfuStFnU_210.0_360.0.mp4' 2>/dev/null
echo '6bad7c178fe0e87f3039a6c16b167c2d032da2137d8cdf03593404c3fd97efbe' | tr -d '
' > /tmp/exp_P04.txt
H=$(sha256sum 'round6_score_alignment/p1b/media/QPcwfuStFnU_210.0_360.0.mp4' | cut -d' ' -f1)
if [ "$H" = "$(cat /tmp/exp_P04.txt)" ]; then echo "P04 SHA_MATCH $H"; else echo "P04 SHA_MISMATCH got=$H expected=$(cat /tmp/exp_P04.txt)"; fi
echo '--- P05 Snpclpo7Ono_210.0_360.0.mp4'
timeout 300 ssh -o BatchMode=yes aic-inspur-home "cat '/home/inspur/aic_video_data/videos/s/Snpclpo7Ono_210.0_360.0.mp4'" > 'round6_score_alignment/p1b/media/Snpclpo7Ono_210.0_360.0.mp4' 2>/dev/null
echo 'e01cb649f2ff19eb93c8dd5a773e5daa99d57f414ccadab2e380205d68d4fc01' | tr -d '
' > /tmp/exp_P05.txt
H=$(sha256sum 'round6_score_alignment/p1b/media/Snpclpo7Ono_210.0_360.0.mp4' | cut -d' ' -f1)
if [ "$H" = "$(cat /tmp/exp_P05.txt)" ]; then echo "P05 SHA_MATCH $H"; else echo "P05 SHA_MISMATCH got=$H expected=$(cat /tmp/exp_P05.txt)"; fi
echo '--- P06 Xm1ouND-aiQ_210.0_360.0.mp4'
timeout 300 ssh -o BatchMode=yes aic-inspur-home "cat '/home/inspur/aic_video_data/videos/x/Xm1ouND-aiQ_210.0_360.0.mp4'" > 'round6_score_alignment/p1b/media/Xm1ouND-aiQ_210.0_360.0.mp4' 2>/dev/null
echo 'c4375a95f042ebf40889c0a088255dbb1c73342a7f0d25c18191bdf426a1216e' | tr -d '
' > /tmp/exp_P06.txt
H=$(sha256sum 'round6_score_alignment/p1b/media/Xm1ouND-aiQ_210.0_360.0.mp4' | cut -d' ' -f1)
if [ "$H" = "$(cat /tmp/exp_P06.txt)" ]; then echo "P06 SHA_MATCH $H"; else echo "P06 SHA_MISMATCH got=$H expected=$(cat /tmp/exp_P06.txt)"; fi
echo '--- P07 dEuxoRj0G5Y_210.0_360.0.mp4'
timeout 300 ssh -o BatchMode=yes aic-inspur-home "cat '/home/inspur/aic_video_data/videos/d/dEuxoRj0G5Y_210.0_360.0.mp4'" > 'round6_score_alignment/p1b/media/dEuxoRj0G5Y_210.0_360.0.mp4' 2>/dev/null
echo 'e8c410e21d5d2e75c5533f2b162c6c9ede01e109b6e30316c0395d1ff26be45a' | tr -d '
' > /tmp/exp_P07.txt
H=$(sha256sum 'round6_score_alignment/p1b/media/dEuxoRj0G5Y_210.0_360.0.mp4' | cut -d' ' -f1)
if [ "$H" = "$(cat /tmp/exp_P07.txt)" ]; then echo "P07 SHA_MATCH $H"; else echo "P07 SHA_MISMATCH got=$H expected=$(cat /tmp/exp_P07.txt)"; fi
echo '--- P08 vvT-gqzwUxA_60.0_210.0.mp4'
timeout 300 ssh -o BatchMode=yes aic-inspur-home "cat '/home/inspur/aic_video_data/videos/v/vvT-gqzwUxA_60.0_210.0.mp4'" > 'round6_score_alignment/p1b/media/vvT-gqzwUxA_60.0_210.0.mp4' 2>/dev/null
echo '2f8462e601fd4471dd5779a4fdeea9b72f22e2a89e9cc9b8e825da63cdddc993' | tr -d '
' > /tmp/exp_P08.txt
H=$(sha256sum 'round6_score_alignment/p1b/media/vvT-gqzwUxA_60.0_210.0.mp4' | cut -d' ' -f1)
if [ "$H" = "$(cat /tmp/exp_P08.txt)" ]; then echo "P08 SHA_MATCH $H"; else echo "P08 SHA_MISMATCH got=$H expected=$(cat /tmp/exp_P08.txt)"; fi
