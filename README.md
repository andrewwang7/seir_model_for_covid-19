# seir_model_for_covid-19

## 模型
採用SEIR模型，參考 https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology  模型僅供研究，請理性討論。


## 資料
確診人數資料來源: https://github.com/CSSEGISandData/COVID-19 ，更新時間為台灣時間中午12:50，因此人數比台灣每天下午兩點記者會公布的資料落後近1天。  
  
  
## 程式與概念 
1. 安裝相關套件直接執行run_dl_analysis.py 即可。  
2. SEIR模型主要是擬合已公布的感染人數 (=確診人數-死亡人數-恢復人數)。   
3. 此模型有一個很大的假設，總體影響人數是固定的，這邊取台灣全部人口的0.03% (wiki裡面提到的N)，此數值跟打疫苗、戴口罩、隔離的程度高度相關，這個數字目前不知如何正確取得，是試出來的。   
4. 潛伏期設定為5.5，參照照台灣CDC的Q&A中的5~6天 (https://www.cdc.gov.tw/Category/QAPage/B5ttQxRgFUZlRFPS1dRliw)。   

因此程式中主要影響的參數包括  
optim_days = 40   # 擬合感染人數的天數  
latent_period = 5.5   # 潛伏期  
ratio_population = 0.0003 # 受影響的全人口比例   

註解:  
1. 2020年初此模型是大幅高估，預測結果僅供參考，疫情數據以台灣CDC公告為主，疫情控制需要全體國民共同努力。   
2. 目前只有測試台灣的可以跑，其他國家或地區已經沒有維護了。 
 
 
  

<範例結果>    
![image](https://github.com/andrewwang7/seir_model_for_covid-19/blob/master/~result/Taiwan.png)
