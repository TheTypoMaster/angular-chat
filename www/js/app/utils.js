var scrH = 0;
utils = {
 
        parse_str: function parse_str(pars,str){
            
            for (var key in pars) {
                var f = str.replace(key,pars[key]);
            }
            return f;

        },

        prepare_url: function prepare_url(str,lst){
            for (var key in lst) {
                str = str.replace(key,lst[key])
            }
            str = str.replace('[server]',local_config.signal_server)
            str = str.replace('[app_name]',local_config.app_name)
            if(str.indexOf("http://") == -1) {
                url = 'http://'+str
            } else {
                url = str
            }
            return url


        }

 
}

function scroolldown(){

     scrH = 0;
                setTimeout(function(){
                    $(document).find('.live_write').each(function(index, el) {
                        scrH = scrH + $(this).outerHeight(true);
                    });
                    $('#chat_content').find('.ms_bar').mCustomScrollbar("scrollTo", 'bottom');
                    $('#chat_content').find('.ms_bar').stop().animate({
                        scrollTop: scrH
                    }, 100);
                },400);
        

    
}




function log() {
  try {
    console.log.apply(console, arguments);                  //#1
  }
  catch(e) {                                                //#2
    try {
      opera.postError.apply(opera, arguments);              //#3
    }
    catch(e){
      alert(Array.prototype.join.call( arguments, " "));    //#4
    }
  }
}







    
