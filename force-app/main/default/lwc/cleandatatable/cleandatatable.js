import { LightningElement, api } from 'lwc';

export default class Cleandatatable extends LightningElement {
    // Recebe a lista de contas do Flow
    @api objeto;

    get existeRegistros(){
        return this.objeto.length;
    }
}