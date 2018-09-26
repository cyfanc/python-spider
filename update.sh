#/bin/bash

#拷贝图片
for i in `ls ./img`
do
	path=`echo "$i"|awk -F '[.]' '{print int($1)}'`
	mv ./img/$i ./music/$path/	
done
rm -rf img

#修改期刊名称
count=`ls|grep *.txt|wc -l`
for((i=0;i<$count;i++))
do
	while read line
	do
		music=`echo "$line"|awk '{print $1}'`
		if [ "$music" == "@vol" ];then
			folder=`echo "$line"|awk '{print int($2)}'`
			rename=`echo "$line"|awk '{print $3}'`
			if [ $folder -lt 10 ];then
				No="00""$folder"
			elif [ $folder -lt 100 ];then
				No="0""$folder"
			else
				No="$folder"
			fi
			echo "mv ./music/$folder ./music/$No$rename"
			mv ./music/$folder ./music/$No$rename
		fi	
	done < result$i.txt
done
