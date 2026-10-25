import { LightningElement } from "lwc";
export default class DevSreDeliveryHub extends LightningElement {
  handleMappingChange() {
    this.template.querySelector("c-dev-sre-deployments")?.refresh();
    this.template.querySelector("c-dev-sre-pipeline-overview")?.refresh();
  }
}
