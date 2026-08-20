"""
邮件发送工具模块
支持发送纯文本、HTML、带附件邮件
"""
import json
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


def get_email_config():
    """获取邮件配置信息"""
    from coze_workload_identity import Client
    client = Client()
    email_credential = client.get_integration_credential("integration-email-imap-smtp")
    return json.loads(email_credential)


def _create_email_message(subject: str, content: str, from_name: str, to_addrs: list, 
                          cc_addrs: list = None, bcc_addrs: list = None) -> tuple:
    """创建邮件消息对象"""
    config = get_email_config()
    
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((from_name, config["account"]))
    msg["To"] = ", ".join(to_addrs) if to_addrs else ""
    
    recipients = to_addrs.copy() if to_addrs else []
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
        recipients.extend(cc_addrs)
    if bcc_addrs:
        recipients.extend(bcc_addrs)
    
    msg["Subject"] = Header(subject, "utf-8")
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    
    # 添加纯文本和HTML内容
    text_part = MIMEText(content, "plain", "utf-8")
    
    # 构建专业HTML内容
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>学习助手邮件</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; background-color: #f0f2f5;">
        <div style="max-width: 600px; margin: 30px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
            <!-- 头部区域 -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 35px 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 600;">📚 学习助手</h1>
            </div>
            
            <!-- 内容区域 -->
            <div style="padding: 30px;">
                <div style="background-color: #f8f9fa; border-radius: 10px; padding: 25px;">
                    <pre style="font-family: inherit; white-space: pre-wrap; word-wrap: break-word; margin: 0; color: #2c3e50; line-height: 1.8; font-size: 15px;">{content}</pre>
                </div>
            </div>
            
            <!-- 页脚 -->
            <div style="background-color: #2c3e50; padding: 20px; text-align: center;">
                <p style="margin: 0; color: #bdc3c7; font-size: 12px;">
                    由学习伙伴智能助手生成 · 祝你学习愉快！🌟
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(text_part)
    msg.attach(html_part)
    
    return msg, recipients, config


@tool
def send_text_email(subject: str, content: str, to_addrs: list, 
                    from_name: str = "学习助手", cc_addrs: list = None) -> str:
    """
    发送纯文本邮件。
    
    Args:
        subject: 邮件主题
        content: 邮件正文内容（纯文本）
        to_addrs: 收件人列表，如 ["recipient@example.com"]
        from_name: 发件人显示名称
        cc_addrs: 抄送列表，可选
    
    Returns:
        发送结果 JSON 字符串
    """
    ctx = request_context.get() or new_context(method="send_text_email")
    
    try:
        msg, recipients, config = _create_email_message(subject, content, from_name, to_addrs, cc_addrs)
        
        if not recipients:
            return json.dumps({"status": "error", "message": "收件人为空"})
        
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        attempts = 3
        last_err = None
        
        for i in range(attempts):
            try:
                with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=ctx, timeout=30) as server:
                    server.ehlo()
                    server.login(config["account"], config["auth_code"])
                    server.sendmail(config["account"], recipients, msg.as_string())
                return json.dumps({
                    "status": "success", 
                    "message": f"邮件发送成功",
                    "recipient_count": len(to_addrs),
                    "recipients": to_addrs
                })
            except Exception as e:
                last_err = e
                time.sleep(1 * (i + 1))
        
        return json.dumps({
            "status": "error", 
            "message": f"发送失败: {str(last_err)}"
        })
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"发送失败: {str(e)}"})


@tool
def send_html_email(subject: str, html_content: str, to_addrs: list,
                     from_name: str = "学习助手", cc_addrs: list = None) -> str:
    """
    发送HTML格式邮件。
    
    Args:
        subject: 邮件主题
        html_content: HTML格式的邮件正文
        to_addrs: 收件人列表
        from_name: 发件人显示名称
        cc_addrs: 抄送列表，可选
    
    Returns:
        发送结果 JSON 字符串
    """
    ctx = request_context.get() or new_context(method="send_html_email")
    
    try:
        config = get_email_config()
        
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((from_name, config["account"]))
        msg["To"] = ", ".join(to_addrs) if to_addrs else ""
        
        recipients = to_addrs.copy() if to_addrs else []
        if cc_addrs:
            msg["Cc"] = ", ".join(cc_addrs)
            recipients.extend(cc_addrs)
        
        msg["Subject"] = Header(subject, "utf-8")
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        if not recipients:
            return json.dumps({"status": "error", "message": "收件人为空"})
        
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        attempts = 3
        last_err = None
        
        for i in range(attempts):
            try:
                with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=ssl_ctx, timeout=30) as server:
                    server.ehlo()
                    server.login(config["account"], config["auth_code"])
                    server.sendmail(config["account"], recipients, msg.as_string())
                return json.dumps({
                    "status": "success", 
                    "message": f"HTML邮件发送成功",
                    "recipient_count": len(to_addrs)
                })
            except Exception as e:
                last_err = e
                time.sleep(1 * (i + 1))
        
        return json.dumps({
            "status": "error", 
            "message": f"发送失败: {str(last_err)}"
        })
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"发送失败: {str(e)}"})


@tool
def send_email_with_image(subject: str, content: str, image_urls: list, 
                          to_addrs: list, from_name: str = "学习助手", 
                          cc_addrs: list = None) -> str:
    """
    发送包含图片引用的邮件。
    
    Args:
        subject: 邮件主题
        content: 邮件正文描述
        image_urls: 图片URL列表，图片将嵌入HTML中显示
        to_addrs: 收件人列表
        from_name: 发件人显示名称
        cc_addrs: 抄送列表，可选
    
    Returns:
        发送结果 JSON 字符串
    """
    ctx = request_context.get() or new_context(method="send_email_with_image")
    
    try:
        config = get_email_config()
        
        # 构建专业HTML内容
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; background-color: #f5f6fa;">
            <div style="max-width: 650px; margin: 30px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                <!-- 头部区域 -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 35px 30px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">📚 {subject}</h1>
                </div>
                
                <!-- 内容区域 -->
                <div style="padding: 30px;">
                    <!-- 内容描述 -->
                    <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                        <p style="margin: 0; color: #2c3e50; font-size: 15px; line-height: 1.8;">{content}</p>
                    </div>
                    
                    <!-- 图片画廊 -->
                    <div style="margin-top: 20px;">
                        <h3 style="color: #2c3e50; font-size: 16px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #667eea;">
                            🖼️ 图片展示
                        </h3>
        """
        
        for idx, img_url in enumerate(image_urls):
            # 为图片生成更友好的描述
            html_body += f"""
                        <div style="margin-bottom: 25px; background-color: #ffffff; border: 1px solid #e8e8e8; border-radius: 10px; overflow: hidden;">
                            <div style="background-color: #f8f9fa; padding: 12px 18px; border-bottom: 1px solid #e8e8e8;">
                                <span style="color: #667eea; font-weight: 600;">📷 图片 {idx + 1}</span>
                            </div>
                            <div style="padding: 15px; text-align: center;">
                                <img src="{img_url}" alt="图片{idx + 1}" style="max-width: 100%; height: auto; border-radius: 6px; display: inline-block;">
                            </div>
                        </div>
            """
        
        html_body += """
                        <!-- 底部提示 -->
                        <div style="margin-top: 30px; padding: 18px; background-color: #e8f4fd; border-radius: 10px; border-left: 4px solid #667eea;">
                            <p style="margin: 0; color: #34495e; font-size: 14px;">
                                💡 <strong>提示：</strong>点击图片可查看大图，如图片无法显示请联系管理员。
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- 页脚 -->
                <div style="background-color: #2c3e50; padding: 20px; text-align: center;">
                    <p style="margin: 0; color: #bdc3c7; font-size: 12px;">
                        由学习伙伴智能助手生成 · 祝你学习愉快！🌟
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((from_name, config["account"]))
        msg["To"] = ", ".join(to_addrs) if to_addrs else ""
        
        recipients = to_addrs.copy() if to_addrs else []
        if cc_addrs:
            msg["Cc"] = ", ".join(cc_addrs)
            recipients.extend(cc_addrs)
        
        msg["Subject"] = Header(subject, "utf-8")
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        
        msg.attach(MIMEText(content, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        if not recipients:
            return json.dumps({"status": "error", "message": "收件人为空"})
        
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        attempts = 3
        last_err = None
        
        for i in range(attempts):
            try:
                with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=ssl_ctx, timeout=30) as server:
                    server.ehlo()
                    server.login(config["account"], config["auth_code"])
                    server.sendmail(config["account"], recipients, msg.as_string())
                return json.dumps({
                    "status": "success", 
                    "message": f"带图片邮件发送成功",
                    "images_count": len(image_urls),
                    "recipient_count": len(to_addrs)
                })
            except Exception as e:
                last_err = e
                time.sleep(1 * (i + 1))
        
        return json.dumps({
            "status": "error", 
            "message": f"发送失败: {str(last_err)}"
        })
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"发送失败: {str(e)}"})


@tool
def send_learning_plan_email(to_email: str, subject: str, plan_content: str, 
                             attachments: list = None, image_urls: list = None) -> str:
    """
    发送学习计划邮件，支持附件和图片。
    
    Args:
        to_email: 收件人邮箱地址
        subject: 邮件主题（如：您的Python学习计划）
        plan_content: 学习计划正文内容
        attachments: 附件文件路径列表（如PDF文件），可选
        image_urls: 思维导图等图片URL列表，可选
    
    Returns:
        发送结果 JSON 字符串
    """
    ctx = request_context.get() or new_context(method="send_learning_plan_email")
    
    try:
        config = get_email_config()
        
        msg = MIMEMultipart()
        msg["From"] = formataddr(("📚 学习助手", config["account"]))
        msg["To"] = to_email
        msg["Subject"] = Header(subject, "utf-8")
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()
        
        # 构建专业HTML内容
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; background-color: #f0f2f5;">
            <div style="max-width: 700px; margin: 30px auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 30px rgba(0,0,0,0.1);">
                <!-- 头部区域 -->
                <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 40px 30px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 26px; font-weight: 700;">📚 {subject}</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px;">🌟 制定时间：{time.strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                
                <!-- 内容区域 -->
                <div style="padding: 35px;">
                    <!-- 学习计划内容 -->
                    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; padding: 25px; margin-bottom: 30px;">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <span style="font-size: 24px; margin-right: 10px;">📋</span>
                            <h3 style="color: #11998e; margin: 0; font-size: 18px;">学习计划详情</h3>
                        </div>
                        <div style="background-color: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <pre style="font-family: inherit; white-space: pre-wrap; word-wrap: break-word; margin: 0; color: #2c3e50; line-height: 1.8; font-size: 14px;">{plan_content}</pre>
                        </div>
                    </div>
        """
        
        # 添加图片画廊
        if image_urls:
            html_body += f"""
                    <!-- 图片画廊区域 -->
                    <div style="margin-top: 25px;">
                        <div style="display: flex; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #11998e;">
                            <span style="font-size: 24px; margin-right: 10px;">📊</span>
                            <h3 style="color: #11998e; margin: 0; font-size: 18px;">相关图表展示</h3>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
            """
            for idx, img_url in enumerate(image_urls):
                # 根据图片索引生成不同类型的标题
                titles = ["学习进度图", "知识结构图", "能力分析图", "统计图表"]
                title = titles[idx] if idx < len(titles) else f"图表 {idx + 1}"
                
                html_body += f"""
                            <div style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); transition: transform 0.3s;">
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 12px 18px;">
                                    <span style="color: #ffffff; font-weight: 600; font-size: 14px;">📈 {title}</span>
                                </div>
                                <div style="padding: 15px;">
                                    <img src="{img_url}" alt="{title}" style="width: 100%; height: auto; border-radius: 8px; display: block;">
                                </div>
                            </div>
                """
            
            html_body += """
                        </div>
                    </div>
            """
        
        # 添加温馨提示
        html_body += """
                    <!-- 温馨提示 -->
                    <div style="margin-top: 35px; padding: 25px; background: linear-gradient(135deg, #e8f8f5 0%, #d5f5e3 100%); border-radius: 12px; border: 1px solid #abebc6;">
                        <div style="display: flex; align-items: flex-start;">
                            <span style="font-size: 28px; margin-right: 15px;">💡</span>
                            <div>
                                <h4 style="color: #11998e; margin: 0 0 10px 0; font-size: 16px;">学习小贴士</h4>
                                <ul style="margin: 0; padding-left: 20px; color: #2c3e50; line-height: 2; font-size: 14px;">
                                    <li>制定合理的学习计划，每天坚持学习</li>
                                    <li>理论与实践相结合，多动手编程</li>
                                    <li>遇到问题及时记录，可以随时向我提问</li>
                                    <li>定期回顾所学知识，巩固学习成果</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 页脚 -->
                <div style="background-color: #2c3e50; padding: 25px; text-align: center;">
                    <p style="margin: 0 0 8px 0; color: #ffffff; font-size: 15px; font-weight: 600;">
                        🌟 学习伙伴智能助手
                    </p>
                    <p style="margin: 0; color: #bdc3c7; font-size: 12px;">
                        祝你学习愉快，期待你的成长与进步！
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 添加纯文本备选
        msg.attach(MIMEText(plan_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        # 添加附件
        if attachments:
            from email.mime.base import MIMEBase
            from email import encoders
            
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        filename = file_path.split("/")[-1]
                        part.add_header("Content-Disposition", f"attachment; filename={filename}")
                        msg.attach(part)
                except Exception:
                    continue
        
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        attempts = 3
        last_err = None
        
        for i in range(attempts):
            try:
                with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=ssl_ctx, timeout=30) as server:
                    server.ehlo()
                    server.login(config["account"], config["auth_code"])
                    server.sendmail(config["account"], [to_email], msg.as_string())
                
                return json.dumps({
                    "status": "success", 
                    "message": f"学习计划邮件发送成功",
                    "recipient": to_email,
                    "has_attachments": len(attachments) if attachments else 0,
                    "has_images": len(image_urls) if image_urls else 0
                })
            except Exception as e:
                last_err = e
                time.sleep(1 * (i + 1))
        
        return json.dumps({
            "status": "error", 
            "message": f"发送失败: {str(last_err)}"
        })
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"发送失败: {str(e)}"})


@tool
def test_email_connection() -> str:
    """
    测试邮件连接是否正常。
    
    Returns:
        测试结果 JSON 字符串
    """
    try:
        config = get_email_config()
        
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"], context=ssl_ctx, timeout=10) as server:
            server.ehlo()
            server.login(config["account"], config["auth_code"])
        
        return json.dumps({
            "status": "success",
            "message": "邮件服务连接正常",
            "account": config["account"],
            "smtp_server": config["smtp_server"],
            "imap_server": config["imap_server"]
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"连接失败: {str(e)}"
        })
