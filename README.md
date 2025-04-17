# 1、项目功能(llm logs analysis)
通过启动代理服务，我们可以轻松记录每次请求的参数和返回结果，从而便捷地分析客户端调用大模型的逻辑，实现对现象的理解和本质的透彻认识，做到知其然也知其所以然

# 2、项目背景
在真正的AGI到来之前，我们必将经历一段漫长的旅程，期间需要不断面对挑战，无论是普通人还是专业人士，生活都将因此而改变。

然而，对于大模型的使用，无论是普通用户还是开发人员，往往都是通过各种客户端间接接触的。但客户端往往屏蔽了和大模型交互的过程，可以直接根据用户的简单输入，
就给出结果，给人一种感觉就是大模型很神秘，像黑盒一样。 实际不是这样的，使用大模型，简单理解我们就是在调用一个接口，有输入输出罢了。
需要注意的是，尽管许多推理平台提供了OpenAI格式的接口，但它们的实际支持情况各不相同，简单来说，API的请求参数和返回参数并不完全一致。

若想了解详细参数支持情况，请看

[准标准:OpenAI API](https://platform.openai.com/docs/api-reference/responses/create)

[开发环境常用:OLLAMA API](https://github.com/ollama/ollama/blob/main/docs/openai.md#supported-features)

[生产环境常用:VLLM API](https://github.com/ollama/ollama/blob/main/docs/openai.md#supported-features)

其他平台请自行查阅

### 本项目采用CGI模式提供API服务，以最小的依赖，快速而简洁地运行，致敬经典

# 3、安装所需扩展

```sh
pip install openai
```

# 4、用法
进入根目录，然后进入bin目录
点击run-server.bat,就可以启动cgi服务

或者在跟目录直接运行:
```sh
python server.py #(默认8000端口)

也可以指定端口
python server.py --port=8001
```

启动后当请求该代理服务时，logs目录中会根据日期创建一个文件夹，里面就是详细的日志
# 5、例子
统一把openai的base_url改成该服务的地址：http://127.0.0.1:8000
### a、 langchain chat模式
### 先安装langchain:
```sh
pip install langchain langchain-openai
```

```sh
from langchain.chat_models import init_chat_model
model = init_chat_model("qwen2.5-coder:1.5b", model_provider="openai",base_url='http://127.0.0.1:8000',api_key='ollama')
model.invoke("Hello, world!")
```
运行上面代码后请查看logs目录下的日志

# License
[Apache 2.0 License.](LICENSE)