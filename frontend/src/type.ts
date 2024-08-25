export  interface DialogCreateType {
    name:string,
    agent:string,
}

export  interface AgentCreateType {
    name:string,
    description:string,
    parameter:string,
    code:string,
    logo:any
}

export  interface AgentUpdateType {
    name:string,
    description:string,
    parameter:string,
    code:string,
    logoFile:any
}

export  interface MsgLikeType {
    userInput:string,
    agentOutput:string,
}
