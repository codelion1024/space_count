#!/bin/bash


# the path to save json data file
jsonpath="~/.storagemonitordata"
old_path=$PWD

# the file and dir count function
function FileCount(){
  for file in $(ls "$1")
  do
    if [ -d "$1/$file" ]; then
      echo "    {" >> ${jsonfile}
      local dirpath="$1/$file"
      local dirsize=$(stat -c %s $dirpath)
      let usedsize=usedsize+$dirsize
      dirpath=${dirpath:1}
      # convet "/XXX" and "/DATA" to "/xxx" and "/data"
      dirpath=$(echo $dirpath | tr '[:upper:]' '[:lower:]')

      echo "      \"file_path\":\"$dirpath\"," >> ${jsonfile}
      echo "      \"file_size\":\"$dirsize\"," >> ${jsonfile}
      echo "      \"file_type\":\"dir\"" >> ${jsonfile}
      echo "    }," >> ${jsonfile}
      FileCount "$1/$file"
    else
      if [ ! -L "$1/$file" ]; then # don't stat link file
        echo "    {" >> ${jsonfile}
        local filepath="$1/$file"
        local filesize=$(ls -l $filepath | cut -d ' ' -f 5)
        let usedsize=usedsize+$filesize
        filepath=${filepath:1}
        # convet "/CUST" and "/DATA" to "/cust" and "/data"
        filepath=$(echo $filepath | tr '[:upper:]' '[:lower:]')

        echo "      \"file_path\":\"$filepath\"," >> ${jsonfile}
        echo "      \"file_size\":\"$filesize\"," >> ${jsonfile}
        echo "      \"file_type\":\"file\"" >> ${jsonfile}
        echo "    }," >> ${jsonfile}
      fi
    fi
  done
}


IFS=$'\n'
serverfile=$1


time_stamp=$(date +%Y.%m.%d-%H:%M:%S)
outdir=$(grep "path_to_out" $serverfile | cut -d ' ' -f 2)
device_name=$(grep "^target_product" $serverfile | cut -d ' ' -f 2)
build_success=$(grep "success" $serverfile | cut -d ' ' -f 2)
jsonfile="${jsonpath}/${device_name}-${miui_version}_${is_global}_${time_stamp}.json"
uploadinfo="${jsonpath}/${device_name}-${time_stamp}.txt"
system_total=0
data_total=0
objdir=${outdir}/obj/PACKAGING/target_files_intermediates/${device_name}-target_files
system_total=$(grep "system_size" ${objdir}/META/misc_info.txt | cut -d '=' -f 2)
data_total=$(grep "userdata_size" ${objdir}/META/misc_info.txt | cut -d '=' -f 2)


mkdir -p $jsonpath
if [ -f ${jsonfile} ]; then
    rm -f ${jsonfile}
fi
if [ -f ${uploadinfo} ]; then
    rm -f ${uploadinfo}
fi

echo "{" >> ${jsonfile}
echo "  \"ts\":\"$time_stamp\"," >> ${jsonfile}
echo "  \"success\":\"$build_success\"," >> ${jsonfile}
echo "  \"name\":\"$device_name\"," >> ${jsonfile}
echo "  \"type\":\"$version_type\"," >> ${jsonfile}


# begin statistics the files and dirs in system, data partition
echo "  \"files\":[" >> ${jsonfile}
if [ "$has_cust" == "true" ]; then
    cd $objdir
    usedsize=0
    FileCount "./CUST" $usedsize
    cust_used=$usedsize
else
    cust_used="none"
fi

cd $objdir
usedsize=0
FileCount "./DATA" $usedsize
data_used=$usedsize
cd $outdir
usedsize=0
FileCount "./system" $usedsize
system_used=$usedsize

# according to json format,change the last elemnet's format form "}," to "}"
sed -i '$d' ${jsonfile}
echo "    }" >> ${jsonfile}
echo "  ]," >> ${jsonfile}
# end statistics

echo "  \"st\":\"$system_total\"," >> ${jsonfile}
echo "  \"su\":\"$system_used\"," >> ${jsonfile}
echo "  \"dt\":\"$data_total\"," >> ${jsonfile}
echo "  \"du\":\"$data_used\"," >> ${jsonfile}
echo "  \"ct\":\"$cust_total\"," >> ${jsonfile}
echo "  \"cu\":\"$cust_used\"" >> ${jsonfile}
echo "}" >> ${jsonfile}

uploadresult=$(curl -X POST -H "'Content-type':'application/json', 'charset':'utf-8'" --data-binary @${jsonfile} http://xxx/partitionUpload)
returncode=$(echo $uploadresult | cut -d '"' -f 4)


echo "time_stamp:               ${time_stamp}" >> ${uploadinfo}
echo "outdir:                   ${outdir}" >> ${uploadinfo}
echo "device_name:              ${device_name}" >> ${uploadinfo}
echo "version_type:             ${version_type}" >> ${uploadinfo}
echo "system_total:             ${system_total}" >> ${uploadinfo}
echo "system_used:              ${system_used}" >> ${uploadinfo}
echo "data_total:               ${data_total}" >> ${uploadinfo}
echo "data_used:                ${data_used}" >> ${uploadinfo}
echo "jsonfile:                 ${jsonfile}" >> ${uploadinfo}
echo "uploadresult:             ${uploadresult}" >> ${uploadinfo}
