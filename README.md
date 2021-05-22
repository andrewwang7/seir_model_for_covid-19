# seir_model_for_covid-19

## 模型
採用SEIR模型，參考 https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology   
模型僅供研究，請理性討論。

潛伏期設定為5.5，依照台灣CDC的Q&A (https://www.cdc.gov.tw/Category/QAPage/B5ttQxRgFUZlRFPS1dRliw)  

## 資料
確診人數資料來源: https://github.com/CSSEGISandData/COVID-19  
人數比記者會的資料落後1~2天。

## 程式與概念 
直接執行run_dl_analysis.py 即可。  
SEIR模型主要是擬合已公布的感染人數 (=確診人數-死亡人數-恢復人數)。   
另外，模型有很大影響的參數是人口數，這邊假設全體人口的某一個比例為可能全體最大被感染人數。
程式中的調整參數為ratio_population，這邊設定是台灣整體人口的0.0003為可能被感染的人口，此數值跟打疫苗、戴口罩、隔離的程度高度相關。   


註解:
2020年初此模型是大幅高估，預測結果僅供參考，疫情數據以台灣CDC公告為主。  
疫情控制需要全體國民共同努力  。 

<範例結果>    
![image](https://github.com/andrewwang7/seir_model_for_covid-19/blob/master/~result/Taiwan.png)
