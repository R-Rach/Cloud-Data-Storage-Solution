import os

# clear all files data
for i in range(1,4):
	for j in range(1,4):
		open(os.getcwd()+"/data/main_data/n"+str(i)+"/p"+str(j)+"_temp.json", 'w').close()
		open(os.getcwd()+"/data/main_data/n"+str(i)+"/p"+str(j)+".json", 'w').close()
for i in range(1,4):
	open(os.getcwd()+"/data/secondary_data/p"+str(i)+"_sec.json", 'w').close()