
import streamlit as st
import pandas as pd
import re
from collections import Counter
from datetime import date, timedelta
import io, os

st.set_page_config(page_title="REDLAB AI | 小红书营销工作台",page_icon="🔴",layout="wide")
st.markdown("""<style>.block-container{padding-top:2rem}h1,h2,h3{color:#e84b69}.stButton button{border-radius:10px}</style>""",unsafe_allow_html=True)
st.title("🔴 REDLAB AI")
st.caption("小红书内容洞察 → 营销选题 → 笔记草稿 → 内容排期 | 面试演示项目")
st.info("演示工具：示例数据均为虚构；分析结果仅反映上传样本，不代表小红书平台整体趋势。AI 生成内容发布前须人工审核。")

with st.sidebar:
    st.header("品牌 Brief")
    brand=st.text_input("品牌名称","清醒气泡")
    product=st.text_input("产品名称","0糖气泡水")
    audience=st.text_input("目标人群","18-30岁都市年轻人")
    selling=st.text_area("核心卖点","0糖、清爽口感、适合办公室饮用")
    goal=st.selectbox("营销目标",["新品种草","品牌曝光","互动增长","转化引导"])
    days=st.slider("排期天数",7,30,14)
    st.divider()
    st.caption("AI API 可选：未配置时使用明确标记的模板演示模式。")
    api_key=st.text_input("SiliconFlow API Key（可留空）",type="password")
    model=st.text_input("模型名称","Qwen/Qwen2.5-7B-Instruct")

def ask_ai(task, context):
    if not api_key: return None
    try:
        import requests
        response=requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
            json={"model":model,"messages":[{"role":"system","content":"你是品牌营销分析助手。仅基于用户提供的数据分析，不要捏造真实平台数据、用户反馈、产品功效或保证爆款。输出清晰中文，营销内容需标记为草稿。"},{"role":"user","content":task+"\n"+context}],"temperature":0.6,"max_tokens":1500},
            timeout=45)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"AI 请求失败：{e}。请核对 API Key、模型名称和账户额度。")
        return None

sample=pd.DataFrame([
    ["打工人的下午三点快乐水",1200,430,85],
    ["0糖气泡水办公室饮用分享",930,310,66],
    ["清爽饮品怎么选？",780,250,43],
    ["周末野餐饮品灵感",1460,620,120],
    ["夏日冰饮搭配指南",1880,730,150],
    ["便利店饮料选购记录",650,190,34],
],columns=["标题","点赞","收藏","评论"])

tabs=st.tabs(["📊 爆款分析","🎯 智能选题","✨ 内容工厂","📅 营销日历"])
with tabs[0]:
    st.subheader("笔记数据分析")
    uploaded=st.file_uploader("上传 CSV 或 Excel（需要：标题、点赞、收藏、评论）",type=["csv","xlsx"])
    if uploaded:
        try:
            df=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"读取失败：{e}")
            st.stop()
        source="用户上传数据"
    else:
        df=sample.copy()
        source="虚构示例数据"
    required=["标题","点赞","收藏","评论"]
    if any(c not in df.columns for c in required):
        st.error("缺少必需列："+", ".join(c for c in required if c not in df.columns))
        st.stop()
    df=df.copy()
    for c in required[1:]:
        df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0).clip(lower=0)
    df["标题"]=df["标题"].fillna("").astype(str)
    df["总互动"]=df[["点赞","收藏","评论"]].sum(axis=1)
    st.caption(f"当前数据来源：{source}；总互动=点赞+收藏+评论，不等于互动率（缺少曝光量）。")
    a,b,c=st.columns(3)
    a.metric("样本笔记",len(df))
    b.metric("平均总互动",f"{df['总互动'].mean():,.0f}" if len(df) else "0")
    c.metric("最高总互动",f"{df['总互动'].max():,.0f}" if len(df) else "0")
    st.dataframe(df.sort_values("总互动",ascending=False),use_container_width=True)
    st.bar_chart(df.set_index("标题")["总互动"])
    top=df.nlargest(5,"总互动")
    insight="高互动样本标题："+ "；".join(top["标题"].tolist())
    st.session_state["insight"]=insight
    if st.button("生成内容洞察"):
        context=f"品牌：{brand}；产品：{product}；样本来源：{source}。\n"+df.to_csv(index=False)
        result=ask_ai("请分析样本中的高互动内容特点、可测试选题与样本局限；不得声称因果或平台趋势。",context)
        if result:
            st.markdown(result)
        else:
            st.warning("模板演示模式（非 AI 实时分析）")
            st.write(insight)
            st.write("建议测试：办公场景、生活方式搭配、饮用体验分享；实际效果需 A/B 测试。")
with tabs[1]:
    st.subheader("营销选题生成")
    if st.button("生成 10 个选题"):
        context=f"品牌：{brand}；产品：{product}；受众：{audience}；卖点：{selling}；目标：{goal}；样本洞察：{st.session_state.get('insight','未上传数据')}"
        result=ask_ai("生成10个小红书选题，每个含标题、切入角度、内容形式、互动引导，避免虚构测评体验。",context)
        if result:
            st.session_state["topics"]=result
        else:
            angles=["办公室下午茶","通勤随身饮品","周末野餐","低糖饮品选择","夏日冰饮","便利店选购","朋友聚会","运动后补水场景","工作日解压","新口味尝鲜"]
            st.session_state["topics"]="【模板演示，非 AI 实时生成】\n\n"+"\n".join(f"{i}. {product}｜{angle}：图文场景分享，邀请评论自己的选择。" for i,angle in enumerate(angles,1))
    if "topics" in st.session_state:
        st.markdown(st.session_state["topics"])
        st.download_button("下载选题 TXT",st.session_state["topics"],file_name="topics.txt")
with tabs[2]:
    st.subheader("小红书内容工厂")
    topic=st.text_input("输入选题","打工人的下午三点饮品灵感")
    tone=st.selectbox("文案风格",["真实分享","轻松活泼","专业科普","简洁种草"])
    if st.button("生成笔记草稿"):
        context=f"品牌：{brand}；产品：{product}；受众：{audience}；卖点：{selling}；选题：{topic}；风格：{tone}"
        result=ask_ai("生成5个标题、1篇200字以内的小红书笔记草稿、5个话题标签、封面创意和人工审核清单；不得伪装真实亲测、编造功效。",context)
        if result:
            st.session_state["note"]=result
        else:
            st.session_state["note"]=f"""【模板演示，非 AI 实时生成】\n\n标题备选：\n1. {topic}\n2. 办公室饮品灵感｜{product}\n3. 忙碌工作日的清爽选择\n4. 最近在关注哪些饮品？\n5. {product}的搭配思路\n\n正文草稿：\n最近在整理适合工作日的饮品清单，发现{product}可以作为一个选项。产品资料标注的卖点包括：{selling}。你平时更喜欢哪种口味？欢迎分享！\n\n#饮品灵感 #办公室日常 #生活方式 #新品分享 #品牌内容\n\n封面：产品静物+办公桌场景。\n审核：核对产品卖点与标签；确认素材授权；不得虚构个人体验或效果。"""
    if "note" in st.session_state:
        st.text_area("可复制编辑的草稿",st.session_state["note"],height=360)
        st.download_button("下载笔记 TXT",st.session_state["note"],file_name="note.txt")
with tabs[3]:
    st.subheader("营销内容日历")
    start=st.date_input("开始日期",date.today())
    if st.button("生成排期"):
        themes=["新品亮相","办公场景","产品卖点解读","生活方式搭配","常见问题","用户互动","内容回顾"]
        dates=[start+timedelta(days=i) for i in range(days)]
        calendar=pd.DataFrame([{"日期":d.isoformat(),"主题":themes[i%len(themes)],"形式":"图文" if i%3 else "短视频","目标":goal,"状态":"待人工审核"} for i,d in enumerate(dates)])
        st.session_state["calendar"]=calendar
    if "calendar" in st.session_state:
        calendar=st.session_state["calendar"]
        st.caption("规则生成排期（非 AI 优化），具体发布时间需结合账号数据调整。")
        st.dataframe(calendar,use_container_width=True)
        st.download_button("下载排期 CSV",calendar.to_csv(index=False).encode("utf-8-sig"),file_name="redlab_calendar.csv",mime="text/csv")
st.divider()
st.caption("REDLAB AI · 面试作品原型 · 非小红书官方工具 · 不自动抓取或发布内容")
