/*
这是异想之旅使用的服务器切换js，适用于多台服务器部署场景。
如果你没有此需求，请删除该文件或删除index.html中调用此js文件的语句。
*/
$(function(){
    let server_span_index, server_span_upload_and_newfolder;
    if (location.host === "pan.yixiangzhilv.com") {
        server_span_index = "<span id=\"currentServer\" title=\"点我可切换服务器；服务器之间的文件不互通（用户账号通用）\">\n" +
            "当前服务器：阿里云服务器\n" +
            "</span>";
        server_span_upload_and_newfolder = "<span title=\"服务器之间的文件不互通，请选择自己需要的服务器：文件偏大的请使用异想之旅自建服务器，文件较小、要求稳定性的请使用阿里云服务器（用户账号通用）。\">\n" +
            "当前服务器：阿里云服务器\n" +
            "</span>";
    }else if(location.host === "pan.yxzl.top:8000"){
        server_span_index = "<span id=\"currentServer\" title=\"点我可切换服务器；服务器之间的文件不互通（用户账号通用）\">\n" +
            "当前服务器：异想之旅自建服务器\n" +
            "</span>";
        server_span_upload_and_newfolder = "<span title=\"服务器之间的文件不互通，请选择自己需要的服务器：文件偏大的请使用异想之旅自建服务器，文件较小、要求稳定性的请使用阿里云服务器（用户账号通用）。\">\n" +
            "当前服务器：异想之旅自建服务器\n" +
            "</span>";
    }else{
        server_span_index = "<span id=\"currentServer\" title=\"点我可切换服务器；服务器之间的文件不互通（用户账号通用）\">\n" +
            "当前服务器：本地或测试服务器\n" +
            "</span>";
        server_span_upload_and_newfolder = "<span title=\"服务器之间的文件不互通，请选择自己需要的服务器：文件偏大的请使用异想之旅自建服务器，文件较小、要求稳定性的请使用阿里云服务器（用户账号通用）。\">\n" +
            "当前服务器：本地或测试服务器\n" +
            "</span>";
    }
    $("#page-info").append(server_span_index);
    $("#serverinfo_of_upload").append(server_span_upload_and_newfolder);
    $("#serverinfo_of_newfolder").append(server_span_upload_and_newfolder);


    $("#currentServer").click(function () {
        if(location.host === "pan.yixiangzhilv.com"){
            window.open("http://pan.yxzl.top:8000/", "_top");
        }else if(location.host === "pan.yxzl.top:8000"){
            window.open("https://pan.yixiangzhilv.com/", "_top");
        }else{
            alert("切换服务器失败：找不到其他的服务器或集群机器！")
        }
    })
});

