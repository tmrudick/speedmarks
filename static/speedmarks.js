var speedmarks = function(bookmarklet) {

  var star = new Image();
  star.src = '/static/star.png';
  var gstar = new Image();
  gstar.src = '/static/gray_star.png';
  var share = new Image();
  share.src = '/static/share.png';
  
  var change = true;
  
  var that = {};
  
  function setChange(newChange) {
    change = newChange;
  }
  that.setChange = setChange;
  
  function starMouseOver(item) {
    if (!change) {
      return change = true;
    }
    if (item.src === star.src) {
      item.src = gstar.src;
    } else {
      item.src = star.src;
    }
  }
  that.starMouseOver = starMouseOver;
  
  function shareMouseOver(item) {
    if (item.src == share.src) {
      item.src = '/static/gray_share.png';
    } else {
      item.src = share.src;
    }
  }
  that.shareMouseOver = shareMouseOver;
  
  var currentLink = null;
  function displayShareBox(item) {
    currentLink = item;
    var sharing = $('#sharing > div').clone();
    sharing.attr('id', 'visible-sharing');
    $.facebox(sharing);
    // TODO: set focus
    sharing.find('.share-with').focus();
  }
  that.displayShareBox = displayShareBox;
  
  function shareLink(form) {
    var share = form.find('.share-with').val();
    $.post('/' + bookmarklet + '/share/' + currentLink, {'share': share});
    $.facebox.close();
  }
  that.shareLink = shareLink;
  
  function displayOptions() {
    var options = $('#options > div').clone();
    options.attr('id', 'visible-options');
    $.facebox(options);
    
    $.get('/' + bookmarklet + '/options', function(data) {
      if (data == "") {
        $('#visible-options .allow-sharing').attr('checked', false);
      } else {
        $('#visible-options .allow-sharing').attr('checked', true);
        $('#visible-options .share-name').val(data);
        $('#visible-options .share-name-options').show();
      }
    });
  }
  that.displayOptions = displayOptions;
  
  function enableSharing() {
    if ($('#visible-options .allow-sharing').attr('checked') == true) {
      $('#visible-options .share-name-options').show();
    } else {
      $('#visible-options .share-name-options').hide();
    }
    $.post('/' + bookmarklet + '/options', {'allow': $('#visible-options .allow-sharing').attr('checked')}, function(data) {
      $('#visible-options .share-name').val(data);
    });
  }
  that.enableSharing = enableSharing;
  
  return that;
};