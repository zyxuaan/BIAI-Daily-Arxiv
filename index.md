---
layout: default
title: Arxiv论文总结报告
---

[查看所有摘要归档](archive.md) | 更新日期: 2025-08-20

# Arxiv论文总结报告

## 基本信息
- 生成时间: 2025-08-19 12:28:07
- 使用模型: gemini-2.5-flash
- 论文数量: 4 篇

---

## 论文总结

### [[SIS-Challenge: Event-based Spatio-temporal Instance Segmentation Challenge at the CVPR 2025 Event-based Vision Workshop]](http://arxiv.org/abs/2508.12813v1)
<!-- 2025-08-18 -->
**📅 发布日期**: 2025-08-18

*   **👥 作者**: Friedhelm Hamann, Emil Mededovic, Fabian Gülhan, Yuli Wu, Johannes Stegmaier, Jing He, Yiqing Wang, Kexin Zhang, Lingling Li, Licheng Jiao, Mengru Ma, Hongxiang Huang, Yuhao Yan, Hongwei Ren, Xiaopeng Lin, Yulong Huang, Bojun Cheng, Se Hyun Lee, Gyu Sung Ham, Kanghan Oh, Gi Hyun Lim, Boxuan Yang, Bowen Du, Guillermo Gallego
*   **🎯 研究目的**: 本文旨在概述在CVPR 2025事件视觉研讨会期间举办的时空实例分割（SIS）挑战赛。该挑战的核心目标是推动事件相机和灰度相机数据融合在像素级目标分割方面的研究，解决从异构传感器数据中准确预测定义对象类别像素级分割掩码的难题，并为该领域提供一个性能评估的基准。
*   **⭐ 主要发现**: 论文详细介绍了SIS挑战赛的任务、所使用的数据集、挑战的详细规则和最终结果。此外，文章还深入描述了在挑战赛中排名前五的团队所采用的方法。这些信息为事件相机数据在实例分割领域的应用提供了宝贵的基准和方法参考，展示了融合多模态数据进行高精度时空实例分割的潜力，并促进了相关算法和技术的进步。

---

### [[HOMI: Ultra-Fast EdgeAI platform for Event Cameras]](http://arxiv.org/abs/2508.12637v1)
<!-- 2025-08-18 -->
**📅 发布日期**: 2025-08-18

*   **👥 作者**: Shankaranarayanan H, Satyapreet Singh Yadav, Adithya Krishna, Ajay Vikram P, Mahesh Mehendale, Chetan Singh Thakur
*   **🎯 研究目的**: 尽管事件相机凭借其异步操作和稀疏的事件驱动输出，在需要快速高效闭环控制的边缘机器人应用（如手势人机交互）中具有显著优势，但现有事件处理解决方案仍存在端到端实现不足、延迟高以及未能充分利用事件数据稀疏性等局限。本研究旨在开发一个超低延迟、端到端的边缘AI平台，以克服这些限制，充分发挥事件相机的潜力。
*   **⭐ 主要发现**: 论文介绍了HOMI，一个超低延迟、端到端的边缘AI平台。该平台由Prophesee IMX636事件传感器芯片和Xilinx Zynq UltraScale+MPSoC FPGA芯片组成，并部署了自主开发的AI加速器。研究团队开发了硬件优化的预处理管道，支持恒定时间处理，并有效利用了事件数据的稀疏性。HOMI的提出为事件相机在边缘计算和实时机器人应用中的广泛部署提供了一个高效且实用的解决方案。

---

### [[Temporal and Rotational Calibration for Event-Centric Multi-Sensor Systems]](http://arxiv.org/abs/2508.12564v1)
<!-- 2025-08-18 -->
**📅 发布日期**: 2025-08-18

*   **👥 作者**: Jiayao Mai, Xiuyuan Lu, Kuan Dai, Shaojie Shen, Yi Zhou
*   **🎯 研究目的**: 事件相机通过响应像素级亮度变化生成异步信号，提供了理论上微秒级延迟的感知范式，有望显著增强多传感器系统的性能。然而，外参标定是有效传感器融合的关键前提，而涉及事件相机的配置仍然是一个研究不足的领域。本研究旨在提出一种专为事件中心多传感器系统设计的、基于运动的时间和旋转标定框架，以消除对专用标定目标的依赖。
*   **⭐ 主要发现**: 论文提出了一种新颖的运动基时间与旋转标定框架，该框架利用从事件相机和其他异构传感器获得的旋转运动估计作为输入，从而避免了对专用标定目标的依赖。与传统依赖事件到帧转换的方法不同，该方法直接处理事件数据，实现了更精确和鲁棒的多传感器系统校准。这对于提升事件相机在复杂多传感器融合系统中的应用性能至关重要，为自动驾驶、机器人导航等领域提供了更可靠的感知基础。

---

### [[Exploring Spatial-Temporal Dynamics in Event-based Facial Micro-Expression Analysis]](http://arxiv.org/abs/2508.11988v1)
<!-- 2025-08-16 -->
**📅 发布日期**: 2025-08-16

*   **👥 作者**: Nicolas Mastropasqua, Ignacio Bugueno-Cordova, Rodrigo Verschae, Daniel Acevedo, Pablo Negri, Maria E. Buemi
*   **🎯 研究目的**: 微表情分析在人机交互和驾驶员监控系统等领域具有重要应用。然而，仅依靠RGB相机捕捉细微快速的面部动作仍然困难，因为其受限于时间分辨率和对运动模糊的敏感性。事件相机提供了微秒级精度、高动态范围和低延迟的替代方案。鉴于目前缺乏包含事件数据和动作单元（Action Unit）的公开数据集，本研究旨在引入一个新的多分辨率、多模态微表情数据集，并探索基于事件数据的微表情时空动态。
*   **⭐ 主要发现**: 本文介绍了一个新颖的、初步的多分辨率、多模态微表情数据集，该数据集在可变光照条件下同步记录了RGB和事件相机数据。研究评估了两个基线任务（动作单元分类），以深入探索微表情的时空动态。这一数据集的发布和基线评估为事件相机在微表情分析领域的进一步研究奠定了基础，并展示了事件数据在捕捉细微、快速面部运动方面的独特优势，有望推动该领域在实时、鲁棒应用中的发展。

---

---

## 生成说明
- 本报告由AI模型自动生成，摘要内容仅供参考。
- 如有错误或遗漏，请以原始论文为准。