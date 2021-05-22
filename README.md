![Taiwan](https://user-images.githubusercontent.com/27774075/119217358-4d8cb200-bb0c-11eb-99dd-610da9bd83a4.png)
# seir_model_for_covid-19

## 模型
採用SEIR模型, 參考 https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology   
模型僅供研究, 請理性討論

潛伏期設定為5.5, 依照台灣CDC的Q&A (https://www.cdc.gov.tw/Category/QAPage/B5ttQxRgFUZlRFPS1dRliw)  

## 資料
確診人數資料來源: https://github.com/CSSEGISandData/COVID-19  
人數比記者會的資料落後1~2天

## 程式與概念 
直接執行run_dl_analysis.py 即可  
SEIR模型主要是擬合已公布的感染人數 (=確診人數-死亡人數-恢復人數)  
另外, 模型有很大影響的參數是人口數, 若封城或戴口罩都會減少感染的人口  
程式中的調整參數為ratio_population  
這邊設定是整體人口的0.0003為可能被感染的人口  


註解:
去年此模型是高估, 預測結果僅供參考, 僅供研究, 疫情數據以台灣CDC公告為主

<範例結果>
![image](https://github.com/andrewwang7/seir_model_for_covid-19/blob/master/~result/Taiwan.png)
