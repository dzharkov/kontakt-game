Array.prototype.firstOrUndefined = function(clause){
    for(var i = 0; i < this.length; i++){
        if(clause(this[i]) === true)
            return this[i];
    }
    return undefined;
}

function User(userData, contactData){
    this.id = userData.id;
    this.isOnline = userData.is_online;
    this.name = userData.nickname;
    this.contact = contactData;
    this.hasContact = (contactData !== undefined);
    this.isMaster = false;
    this.role = "Игрок";

    this.makeMaster = function(){
        this.isMaster = true;
        this.role = "Ведущий";
    }
};

