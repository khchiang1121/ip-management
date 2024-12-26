# IP Manamgement

## 安裝
### 全域設定
```
conda config --add channels conda-forge
```
### 建立環境
```
conda create -n ip python=3.13 "mamba>=0.22.1"
```
### 重新啟動VS CODE
> 不然就算有括號顯示啟動的環境，實際上仍未啟動，套件會裝在錯的地方
### 啟動虛擬環境
```
source ~/anaconda3/etc/profile.d/conda.sh
conda activate ip
```
### 安裝套件
```
mamba install --yes --file requirements.txt
```
## 啟動服務
```
python ./main.py
```
docker compose up --build



python -m venv .venv
source .venv/bin/activate
deactivate
python -m pip install -r requirements.txt

### 產生假資料
```
python ./fake.py
```

### 轉換為excel
```
python ./export_excel.py
```

### 取回ip不一致的資料
```
python get_response.py
```

flask --debug run --host=0.0.0.0 --port=8100
flask --debug run --host=0.0.0.0 --port=8100


# TODO
allow ignore admin ip missing check =>make it configable
ip conflict check
Edit inventor
export data
update server is not complete!!!


- support compare all type in a same time
- support ignore by name when comparing
- remove non-exist key's data from server and cluster details
- show inconsistencies data even if there is no inconsistencies
- add base template to details page
- add view button to the server table and cluser table
- fix network details template when ket does not exist
- [refactor] reorganize network-related classes; move IPNetwork to new module and update references: factory mode!
- server and cluster support all type of network

