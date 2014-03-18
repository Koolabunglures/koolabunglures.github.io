
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Untitled Document</title>
</head>

<body>
<form method="post" action="send.asp">
<p>
 Your Email: <input type="text" name=="FromEmail" />
</p>
<p>
 What is your email address?:
<input type="text" name="ToEmail" />
</p>
<p>
 Your Message: <br />
 <textarea cols="40" rows="5" name="Message">
</textarea>
</p>
 <input type="hidden" name="URL"
 	value="<%= Request.ServerVariables("HTTP_REFERER")%>" />
 <input type="submit" value="Send the Link!" name="SUBMIT" />
 <input type="reset" value="clear" name="RESET" />
</form>
</body>
</html>
