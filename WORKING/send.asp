<%@LANGUAGE="VBSCRIPT" CODEPAGE="65001"%>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>SEND</title>
</head>

<body><%@LANGUAGE="VBSCRIPT"%
<%
	Dim objCDO
	Set objCDO = Server.CreateObject("CDONTS.NewMail")
	
	objCDO.To = Request.Form("ToEmail")
	objCDO.From = Request.Form("FromEmail")
	
	objCDO.bcc = "bloodsoaked-memories.com"
	
	objCDO.Subject = "Check out this great fishing lure website!"
	
	objCDO.Body = strFrom & " has recommended that you check out " _
& "this page at Koolabung Lures:" _
& vbCrLf & vbCrLf & Request.Form("URL") _
& vbCrLf & vbCrLf & Request.Form("message") _
& vbCrLf & vbCrLf & vbCrLf _
& "This page was sent to you using our Send-to-Friend service." _
& "Your email address has not been added to any list of any sort, " _
& "and has not been recorded at our site. "

	objCDO.Send
	Set objCDO = Nothing
%>
</body>
</html>
