# process all texts in LCMC / ZCTC using corenlp to get const/dependency parse results
# Hai Hu Oct. 2017

# reference: https://stackoverflow.com/questions/29764703/stanford-corenlp-process-many-files-with-a-script

dir=~/projects/transPredict/new/data # haiserver
dir=/media/hai/G/MEGA/projects/translationalChinesePred/transPredict/new/data

currTime=`date '+%Y-%m-%d-%H-%M-%S'`

for f in $dir/XIN_sentSplit/XIN*;
do
    echo $f >> filelist-${currTime}.txt
done

java -cp "*" -Xmx10g edu.stanford.nlp.pipeline.StanfordCoreNLP \
-props StanfordCoreNLP-chinese.eachLineIsOneSent.NotSeg.properties \
-filelist filelist-${currTime}.txt -outputDirectory $dir/XIN_corenlp_xml
