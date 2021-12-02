//1.1:	run fixed
//1.1:	uses iDialog.xml from XMS

$.fn.iDialog = function(o) {
	var defaults = {
		load : "",
		run : function() {
		},
		width : "100%",
		height : "100%",
		border : "0",
		windowType : "modal",
		modalOptions : {
			onClose : function() {
				$.modal.close();
				$(this).replaceWith("");
			},
			print : true,
			save : true,
			escClose : true,
			containerCss : {
				height : 600,
				width : 820,
				border : '0px'
			}
		},
		dialogOptions : {
			modal : true
		}
	};

	var o = $.extend(defaults, o);
	var obj = $(this);
	obj.instanceOf = "iDialog";
	obj.version = "1.1";
	obj.releaseDate = "2010-03-22";
	obj.credentials = "beta";
	obj.UId = obj.instanceOf + "_" + obj.get(0).nodeName.toUpperCase() + "_" + obj.attr("id") + "_" + Math.ceil(1000000 * Math.random());
	obj.attr("UID", obj.UId).attr("iof", obj.instanceOf);

	var runsrc = o.run.toString();
	var st = runsrc.indexOf("{") + 1;
	var dr = runsrc.lastIndexOf("}");

	var iFrameContent = $('<iframe id="' + obj.UId + '" width="' + o.width + '" height="' + o.height + '" style="border-width: 0px;"></iframe>');
	var form = $("<form></form>").attr("action", "temp.php?use=templates/iDialog.xml").attr("id", "iDialogForm").attr("name", "iDialogForm").attr("enctype", "multipart/form-data").css("visibility", "hidden").attr("method", "POST");
	var load = $("<textarea></textarea>").attr("name", "load").attr("id", "load").html((o.load)).appendTo(form);
	var run = $("<textarea></textarea>").attr("name", "run").attr("id", "run").html(runsrc.substr(st, dr - st)).appendTo(form);
	var data = $("<textarea></textarea>").attr("name", "data").attr("id", "data").html((obj.html())).appendTo(form);
	var cat = $("<input>").attr("type", "text").attr("name", "cat").attr("id", "cat").attr("value", "iDialog").attr("val", "iDialog").appendTo(form);
	var content = $("<div></div>");
	form.appendTo(content);

	var docHead = ('<html><head></head><body onload="javascript: document.forms[0].submit()">');
	var docFoot = ('</body></html>');

	if (o.windowType == "modal")
		var toreturn = $(iFrameContent).modal(o.modalOptions);
	else
		var toreturn = $(iFrameContent).dialog(o.dialogOptions);

	var iFrameElem = $("iframe#" + obj.UId).get(0);

	iFrameElem.doc().open("text/html", "replace");
	iFrameElem.doc().write(docHead + content.html() + docFoot);
	iFrameElem.doc().close();
	this.dynFrameElem = iFrameElem;

	return toreturn;
}; 